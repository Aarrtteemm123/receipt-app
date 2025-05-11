import asyncio
import sys
from pathlib import Path

from tortoise import Tortoise

# Добавляем родительский каталог (где находится config.py) в sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from config import TORTOISE_ORM
from enums import PaymentTypeEnum
from models import PaymentType


async def init_enums():
    await Tortoise.init(config=TORTOISE_ORM)
    enum_model_map = {
        PaymentTypeEnum: PaymentType,
    }
    for enum_class, model_class in enum_model_map.items():
        for item in enum_class:
            obj, is_created = await model_class.get_or_create(name=item)
            if is_created:
                print("Created", obj)
            else:
                print("Already exist", obj)

    await Tortoise.close_connections()


def main():
    try:
        asyncio.run(init_enums())
    except RuntimeError as e:
        if "Event loop is closed" in str(e):
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(init_enums())


if __name__ == "__main__":
    main()
