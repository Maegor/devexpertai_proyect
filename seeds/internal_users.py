import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from database import SessionLocal, engine, Base
from models import InternalUser, InternalRole

USERS = [
    ("Ana García",       "ana.garcia@devexpert.ai",       InternalRole.Admin),
    ("Carlos López",     "carlos.lopez@devexpert.ai",     InternalRole.Sales),
    ("María Martínez",   "maria.martinez@devexpert.ai",   InternalRole.Finance),
    ("Pedro Sánchez",    "pedro.sanchez@devexpert.ai",    InternalRole.Sales),
    ("Laura Fernández",  "laura.fernandez@devexpert.ai",  InternalRole.Finance),
    ("Javier Rodríguez", "javier.rodriguez@devexpert.ai", InternalRole.Sales),
    ("Sofía Pérez",      "sofia.perez@devexpert.ai",      InternalRole.Admin),
    ("Diego González",   "diego.gonzalez@devexpert.ai",   InternalRole.Sales),
    ("Elena Díaz",       "elena.diaz@devexpert.ai",       InternalRole.Finance),
    ("Miguel Torres",    "miguel.torres@devexpert.ai",    InternalRole.Sales),
    ("Lucía Ramírez",    "lucia.ramirez@devexpert.ai",    InternalRole.Finance),
    ("Andrés Flores",    "andres.flores@devexpert.ai",    InternalRole.Sales),
    ("Carmen Morales",   "carmen.morales@devexpert.ai",   InternalRole.Admin),
    ("Roberto Vargas",   "roberto.vargas@devexpert.ai",   InternalRole.Sales),
    ("Patricia Herrera", "patricia.herrera@devexpert.ai", InternalRole.Finance),
    ("Fernando Jiménez", "fernando.jimenez@devexpert.ai", InternalRole.Sales),
    ("Valentina Castro", "valentina.castro@devexpert.ai", InternalRole.Finance),
    ("Sergio Ortiz",     "sergio.ortiz@devexpert.ai",     InternalRole.Sales),
    ("Natalia Romero",   "natalia.romero@devexpert.ai",   InternalRole.Admin),
    ("Pablo Moreno",     "pablo.moreno@devexpert.ai",     InternalRole.Sales),
    ("Isabel Navarro",   "isabel.navarro@devexpert.ai",   InternalRole.Finance),
    ("Ricardo Silva",    "ricardo.silva@devexpert.ai",    InternalRole.Sales),
    ("Gabriela Ruiz",    "gabriela.ruiz@devexpert.ai",    InternalRole.Finance),
    ("Alejandro Núñez",  "alejandro.nunez@devexpert.ai",  InternalRole.Sales),
    ("Sandra Medina",    "sandra.medina@devexpert.ai",    InternalRole.Admin),
    ("Marcos Aguilar",   "marcos.aguilar@devexpert.ai",   InternalRole.Sales),
    ("Verónica Guzmán",  "veronica.guzman@devexpert.ai",  InternalRole.Finance),
    ("Héctor Reyes",     "hector.reyes@devexpert.ai",     InternalRole.Sales),
    ("Daniela Cruz",     "daniela.cruz@devexpert.ai",     InternalRole.Finance),
    ("Ernesto Vega",     "ernesto.vega@devexpert.ai",     InternalRole.Sales),
]


from seeds.utils import hash_password


async def run():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with SessionLocal() as session:
        from sqlalchemy import select
        for name, email, role in USERS:
            result = await session.execute(
                select(InternalUser).where(InternalUser.email == email)
            )
            if result.scalar_one_or_none():
                print(f"  omitido (ya existe): {email}")
                continue

            user = InternalUser(
                name=name,
                email=email,
                password_hash=hash_password("Password1234!"),
                role=role,
                is_active=True,
            )
            session.add(user)
            print(f"  creado: {email} [{role.value}]")

        await session.commit()

    print(f"\nSeed completado: {len(USERS)} registros procesados.")


if __name__ == "__main__":
    asyncio.run(run())
