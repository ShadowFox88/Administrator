from __future__ import annotations

import asyncio
import dataclasses
import datetime
import functools
import re
from typing import Optional, Set

import asyncpg
import discord
from asyncpg.pool import Pool

from base import custom

STARRED_MESSAGE = re.compile(
    r"\*\*(?P<stars>[0-9]+)\*\* <#(?P<channel>[0-9]+)> ID: (?P<id>[0-9]+)"
)


@dataclasses.dataclass
class Settings:
    recent_id: Optional[int] = None


class StarredMessagePayload:
    __slots__ = (
        "_starboard",
        "message_id",
        "author_id",
        "content",
        "image_url",
        "created_at",
        "stars",
        "channel_id",
        "id"
    )
    JUMP_URL = (
        "https://discord.com/channels/"
        "{self.guild_id}/{self.channel_id}/{self.message_id}"
    )
    IMAGE_TYPES = ("jpg", "png", "gif")

    def __init__(self,
                 starboard: discord.TextChannel,
                 message_id: int,
                 author_id: int,
                 content: str,
                 image_url: Optional[str],
                 created_at: datetime.datetime,
                 stars: int,
                 channel_id: int,
                 id: int):
        self._starboard = starboard
        self.message_id = message_id
        self.author_id = author_id
        self.content = content
        self.image_url = image_url
        self.created_at = created_at
        self.stars = stars
        self.channel_id = channel_id
        self.id = id

    def __hash__(self):
        return hash(self.params)

    def __eq__(self, value):
        if isinstance(value, self.__class__):
            return hash(self) == hash(value)
        return NotImplemented

    def __repr__(self):
        ret = (
            "<StarredMessagePayload message_id={!r} stars={!r} "
            "channel_id={!r} id={!r}>"
        )

        return ret.format(*self.params)

    @classmethod
    def _image_url_from_embed(cls, embed: discord.Embed):
        for value in (embed.image.url, embed.image.proxy_url):
            if value is not embed.Empty:
                return value
        return None

    @classmethod
    def resolve(cls,
                starboard: discord.TextChannel,
                message: discord.Message,
                match: re.Match):
        image_url = None

        if message.embeds:
            embed = message.embeds[0]
            image_url = cls._image_url_from_embed(embed)
        return cls(
            starboard,
            message.id,
            message.author.id,
            message.content,
            image_url,
            message.created_at,
            *map(int, match.groups())
        )

    @property
    def params(self):
        return (
            self.message_id,
            self.author_id,
            self.content,
            self.image_url,
            self.created_at,
            self.stars,
            self.channel_id,
            self.id
        )

    def has_image(self):
        if not self.image_url:
            return False
        lowered = self.image_url.lower()

        return lowered.endswith(self.IMAGE_TYPES)

    def generate_embed(self):
        jump_url = self.JUMP_URL.format(self=self)
        value = f"[Jump!]({jump_url})"
        author = self._starboard.guild.get_member(self.author_id)
        embed = custom.Embed(timestamp=self.timestamp)

        if self.content:
            embed.description = self.content
        embed.set_author(name=author.name, icon_url=author.avatar_url)
        embed.add_field(name="Original", value=value)

        if self.has_image():
            embed.set_image(url=self.image_url)
        return embed

    async def fetch_message(self):
        return await self._starboard.fetch_message(self.message_id)

    async def update(self, *params):
        for attr, param in zip(self.__slots__[1:], params):
            setattr(self, attr, param)


class Database:
    HOME_ID = 336642139381301249
    STARBOARD_ID = 381986593986052107

    def connect(coroutine):
        @functools.wraps(coroutine)
        async def predicate(self, *args, **kwargs):
            async with self.pool.acquire() as conn:
                return await coroutine(self, conn, *args, **kwargs)
        return predicate

    def __init__(self, *, bot, config):
        self.bot = bot
        self.config = config.get("database", config)

        self._loop = asyncio.get_event_loop()
        self._cache_ready = asyncio.Event()
        self.cache: Set = None
        self.pool: Pool = None
        self.settings: Settings = None
        self.starboard: discord.TextChannel = None
        self.init_statement = """
            CREATE SCHEMA IF NOT EXISTS administrator;

            CREATE TABLE IF NOT EXISTS administrator.settings(
                recent_id BIGINT UNIQUE NOT NULL
            );

            CREATE TABLE IF NOT EXISTS administrator.starboard(
                message_id BIGINT UNIQUE PRIMARY KEY NOT NULL,
                author_id BIGINT NOT NULL,
                content TEXT,
                image_url TEXT,
                created_at TIMESTAMP NOT NULL,
                stars INT NOT NULL,
                channel_id BIGINT NOT NULL,
                star_id BIGINT UNIQUE NOT NULL
            );
        """

        self._loop.create_task(self.__ainit__())

    async def __ainit__(self):
        self.pool = await asyncpg.create_pool(**self.config)

        async with self.pool.acquire() as conn:
            await conn.execute(self.init_statement)
        await self.bot.wait_until_ready()
        await self.init_cache()

    @property
    def guild(self):
        return self.bot.get_guild(self.HOME_ID)

    def get(self, **attrs):
        one: bool = attrs.pop("one", False)

        for payload in self.cache:
            for attr, value in attrs.items():
                found = getattr(payload, attr, None)

                if found and found == value:
                    if one:
                        return payload
                    yield payload
        if one:
            return None
        raise StopIteration

    async def wait_until_ready(self):
        return await self._cache_ready.wait()

    @connect
    async def init_cache(self, conn):
        self.bot.log("Initialising starboard cache...")

        i = -1
        query = """
            SELECT
                message_id,
                author_id,
                content,
                image_url,
                created_at,
                stars,
                channel_id,
                star_id
            FROM administrator.starboard;
        """
        records = await conn.fetch(query)
        args = await conn.fetch("SELECT * FROM administrator.settings;")
        self.settings = Settings(*args)
        self.starboard = self.guild.get_channel(self.STARBOARD_ID)
        self.cache = {
            StarredMessagePayload(self.starboard, *args)
            for args in records
        }

        async for message in self.starboard.history(limit=None):
            i += 1
            # rename
            cond = (not self.settings.recent_id or
                    self.settings.recent_id != message.id)

            if i == 0 and cond:
                self.settings.recent_id = message.id
            elif message.id == self.settings.recent_id:
                break

            match = STARRED_MESSAGE.search(message.content)
            obj = StarredMessagePayload.resolve(self.starboard, message, match)

            self.cache.add(obj)
        self._cache_ready.set()

    @connect
    async def save_cache(self, conn):
        params = [p.params for p in self.cache]

        await self.add(*params, bulk=True)

    @connect
    async def add(self,
                  conn,
                  message: discord.Message,
                  match: re.Match):
        statement = """
            INSERT INTO administrator.starboard (
                message_id,
                author_id,
                content,
                image_url,
                created_at,
                stars,
                channel_id,
                star_id
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            ON CONFLICT DO NOTHING;
        """
        obj = StarredMessagePayload.resolve(message, match)

        self.cache.add(obj)
        await conn.execute(statement, obj.params)

    @connect
    async def update(self, conn, content: str, stars: int, id: int):
        statement = """
            UPDATE administrator.starboard
            SET content=$1, stars=$2
            WHERE message_id=$3 OR star_id=$3;
        """
        params = (content, stars, id)
        payload = self.get(id=id)

        await conn.execute(statement, params)
        await payload.update(*params)

    @connect
    async def delete(self, conn, id: int):
        statement = "DELETE FROM administrator.starboard WHERE message_id=$1;"
        params = (
            id,
        )

        await conn.execute(statement, params)

    async def close(self):
        await self.wait_until_ready()
        await self.save_cache()
        await self.pool.close()


def create(*args, **kwargs):
    return Database(*args, **kwargs)
