import asyncio
import random
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy import select
from database import SessionLocal, engine, Base
from models import InternalUser, InternalRole, Partner, PartnerStatus
from seeds.utils import hash_password

PARTNERS_DATA = [
    ("Acme Corp",           "contact@acmecorp.com",          "Acme Corporation",       "acmecorp.com",          "US"),
    ("Blue Ocean Ltd",      "hello@blueocean.io",            "Blue Ocean Ltd",         "blueocean.io",          "GB"),
    ("TechNova",            "info@technova.de",              "TechNova GmbH",          "technova.de",           "DE"),
    ("SunPath Partners",    "partners@sunpath.mx",           "SunPath S.A. de C.V.",   "sunpath.mx",            "MX"),
    ("Apex Solutions",      "apex@apexsol.ca",               "Apex Solutions Inc.",    "apexsol.ca",            "CA"),
    ("Meridian Group",      "hello@meridiangroup.fr",        "Meridian Group SARL",    "meridiangroup.fr",      "FR"),
    ("Orbit Digital",       "team@orbitdigital.es",          "Orbit Digital SL",       "orbitdigital.es",       "ES"),
    ("Vertex Holdings",     "info@vertexholdings.au",        "Vertex Holdings Pty",    "vertexholdings.au",     "AU"),
    ("Pulse Agency",        "contact@pulseagency.br",        "Pulse Agency Ltda.",     "pulseagency.br",        "BR"),
    ("Nexus Partners",      "nexus@nexuspartners.nl",        "Nexus Partners BV",      "nexuspartners.nl",      "NL"),
    ("CloudPeak",           "info@cloudpeak.sg",             "CloudPeak Pte. Ltd.",    "cloudpeak.sg",          "SG"),
    ("Redwood Ventures",    "hello@redwoodventures.us",      "Redwood Ventures LLC",   "redwoodventures.us",    "US"),
    ("Horizon Consulting",  "contact@horizonconsult.it",     "Horizon Consulting SRL", "horizonconsult.it",     "IT"),
    ("Summit Digital",      "team@summitdigital.co",         "Summit Digital Ltd.",    "summitdigital.co",      "CO"),
    ("Aurora Growth",       "info@auroragrowth.se",          "Aurora Growth AB",       "auroragrowth.se",       "SE"),
    ("IronBridge",          "partners@ironbridge.pl",        "IronBridge Sp. z o.o.",  "ironbridge.pl",         "PL"),
    ("CrestLine",           "hello@crestline.pt",            "CrestLine Lda.",         "crestline.pt",          "PT"),
    ("Zenith Global",       "info@zenithglobal.ae",          "Zenith Global FZE",      "zenithglobal.ae",       "AE"),
    ("BlueSky Analytics",   "contact@bluesky.nz",            "BlueSky Analytics Ltd.", "bluesky.nz",            "NZ"),
    ("Atlas Commerce",      "atlas@atlascommerce.in",        "Atlas Commerce Pvt.",    "atlascommerce.in",      "IN"),
    ("Maple Partners",      "info@maplepartners.ca",         "Maple Partners Inc.",    "maplepartners.ca",      "CA"),
    ("Delta Systems",       "hello@deltasystems.kr",         "Delta Systems Co.",      "deltasystems.kr",       "KR"),
    ("Vantage Group",       "vantage@vantagegroup.za",       "Vantage Group (Pty)",    "vantagegroup.za",       "ZA"),
    ("Luminary",            "team@luminary.fi",              "Luminary Oy",            "luminary.fi",           "FI"),
    ("Cascade Digital",     "info@cascadedigital.be",        "Cascade Digital BVBA",   "cascadedigital.be",     "BE"),
    ("PineCrest",           "contact@pinecrest.no",          "PineCrest AS",           "pinecrest.no",          "NO"),
    ("GoldPath",            "hello@goldpath.ch",             "GoldPath AG",            "goldpath.ch",           "CH"),
    ("Silverline Media",    "info@silverlinemedia.at",       "Silverline Media GmbH",  "silverlinemedia.at",    "AT"),
    ("Caspian Tech",        "partners@caspiantech.kz",       "Caspian Tech LLP",       "caspiantech.kz",        "KZ"),
    ("Voyager Agency",      "hello@voyageragency.dk",        "Voyager Agency ApS",     "voyageragency.dk",      "DK"),
    ("Titan Networks",      "info@titannetworks.gr",         "Titan Networks SA",      "titannetworks.gr",      "GR"),
    ("Ember Studios",       "contact@emberstudios.cz",       "Ember Studios s.r.o.",   "emberstudios.cz",       "CZ"),
    ("Keystone",            "team@keystone.ro",              "Keystone SRL",           "keystone.ro",           "RO"),
    ("Clearview Solutions", "info@clearview.hu",             "Clearview Solutions Kft","clearview.hu",          "HU"),
    ("Frontier Digital",    "hello@frontierdigital.cl",      "Frontier Digital SpA",   "frontierdigital.cl",    "CL"),
    ("Solaris Group",       "contact@solarisgroup.ar",       "Solaris Group SA",       "solarisgroup.ar",       "AR"),
    ("Tundra Partners",     "info@tundrapartners.ua",        "Tundra Partners LLC",    "tundrapartners.ua",     "UA"),
    ("Pacific Rim Digital", "team@pacificrim.ph",            "Pacific Rim Digital Inc","pacificrim.ph",         "PH"),
    ("Quartz Advisory",     "hello@quartzadvisory.hk",       "Quartz Advisory Ltd.",   "quartzadvisory.hk",     "HK"),
    ("Monsoon Ventures",    "info@monsoonventures.id",       "Monsoon Ventures PT",    "monsoonventures.id",    "ID"),
    ("CedarBridge",         "contact@cedarbridge.il",        "CedarBridge Ltd.",       "cedarbridge.il",        "IL"),
    ("Icefall",             "hello@icefall.is",              "Icefall ehf.",           "icefall.is",            "IS"),
    ("Sahara Digital",      "info@saharadigital.eg",         "Sahara Digital LLC",     "saharadigital.eg",      "EG"),
    ("Ivory Coast Tech",    "partners@ivorycoasttech.ci",    "IC Tech SARL",           "ivorycoasttech.ci",     "CI"),
    ("Baobab Partners",     "hello@baobabpartners.ng",       "Baobab Partners Ltd.",   "baobabpartners.ng",     "NG"),
    ("Andean Solutions",    "info@andeansolutions.pe",       "Andean Solutions SAC",   "andeansolutions.pe",    "PE"),
    ("Baltic Digital",      "contact@balticdigital.lv",      "Baltic Digital SIA",     "balticdigital.lv",      "LV"),
    ("Adriatic Ventures",   "team@adriaticventures.hr",      "Adriatic Ventures d.o.o","adriaticventures.hr",   "HR"),
    ("Lotus Partners",      "info@lotuspartners.th",         "Lotus Partners Co.",     "lotuspartners.th",      "TH"),
    ("Indigo Consulting",   "hello@indigoconsulting.my",     "Indigo Consulting Sdn.", "indigoconsulting.my",   "MY"),
    ("Evergreen",           "contact@evergreen.vn",          "Evergreen Co. Ltd.",     "evergreen.vn",          "VN"),
    ("Stonewall Digital",   "info@stonewalldigital.ie",      "Stonewall Digital Ltd.", "stonewalldigital.ie",   "IE"),
    ("Cobalt Agency",       "hello@cobaltagency.sk",         "Cobalt Agency s.r.o.",   "cobaltagency.sk",       "SK"),
    ("Amber Digital",       "team@amberdigital.ee",          "Amber Digital OÜ",       "amberdigital.ee",       "EE"),
    ("Velvet Partners",     "info@velvetpartners.lt",        "Velvet Partners UAB",    "velvetpartners.lt",     "LT"),
    ("Cirrus Tech",         "contact@cirrustech.si",         "Cirrus Tech d.o.o.",     "cirrustech.si",         "SI"),
    ("Opal Group",          "hello@opalgroup.bg",            "Opal Group OOD",         "opalgroup.bg",          "BG"),
    ("Onyx Solutions",      "info@onyxsolutions.rs",         "Onyx Solutions d.o.o.",  "onyxsolutions.rs",      "RS"),
    ("Fjord Digital",       "partners@fjorddigital.no",      "Fjord Digital AS",       "fjorddigital.no",       "NO"),
    ("Mirage Media",        "hello@miragemedia.ma",          "Mirage Media SARL",      "miragemedia.ma",        "MA"),
    ("Crescent Partners",   "info@crescentpartners.tr",      "Crescent Partners A.Ş.", "crescentpartners.tr",   "TR"),
    ("Ebony Digital",       "contact@ebonydigital.ke",       "Ebony Digital Ltd.",     "ebonydigital.ke",       "KE"),
    ("Pampas Group",        "team@pampasgroup.uy",           "Pampas Group SA",        "pampasgroup.uy",        "UY"),
    ("Andorra Ventures",    "hello@andorraventures.ad",      "Andorra Ventures SL",    "andorraventures.ad",    "AD"),
    ("Coral Digital",       "info@coraldigital.cu",          "Coral Digital SA",       "coraldigital.cu",       "CU"),
    ("Topaz Partners",      "contact@topazpartners.pk",      "Topaz Partners Pvt.",    "topazpartners.pk",      "PK"),
    ("Meadow Consulting",   "hello@meadowconsulting.ie",     "Meadow Consulting Ltd.", "meadowconsulting.ie",   "IE"),
    ("Rockhill Agency",     "info@rockhillagency.us",        "Rockhill Agency LLC",    "rockhillagency.us",     "US"),
    ("Ironwood Partners",   "team@ironwoodpartners.ca",      "Ironwood Partners Inc.", "ironwoodpartners.ca",   "CA"),
    ("Frostbyte",           "hello@frostbyte.fi",            "Frostbyte Oy",           "frostbyte.fi",          "FI"),
    ("Garnet Digital",      "info@garnetdigital.pt",         "Garnet Digital Lda.",    "garnetdigital.pt",      "PT"),
    ("Jasper Solutions",    "contact@jaspersolutions.mx",    "Jasper Solutions SC",    "jaspersolutions.mx",    "MX"),
    ("Lagoon Partners",     "hello@lagoonpartners.br",       "Lagoon Partners Ltda.",  "lagoonpartners.br",     "BR"),
    ("Marble Agency",       "info@marbleagency.it",          "Marble Agency SRL",      "marbleagency.it",       "IT"),
    ("Nebula Digital",      "team@nebuladigital.es",         "Nebula Digital SL",      "nebuladigital.es",      "ES"),
    ("Obsidian",            "contact@obsidian.fr",           "Obsidian SARL",          "obsidian.fr",           "FR"),
    ("Pebble Partners",     "hello@pebblepartners.au",       "Pebble Partners Pty.",   "pebblepartners.au",     "AU"),
    ("Quill Consulting",    "info@quillconsulting.nl",       "Quill Consulting BV",    "quillconsulting.nl",    "NL"),
    ("Raven Digital",       "team@ravendigital.de",          "Raven Digital GmbH",     "ravendigital.de",       "DE"),
    ("Sapphire Group",      "contact@sapphiregroup.sg",      "Sapphire Group Pte.",    "sapphiregroup.sg",      "SG"),
    ("Teal Partners",       "hello@tealpartners.nz",         "Teal Partners Ltd.",     "tealpartners.nz",       "NZ"),
    ("Umber Digital",       "info@umberdigital.in",          "Umber Digital Pvt.",     "umberdigital.in",       "IN"),
    ("Verdigris",           "team@verdigris.kr",             "Verdigris Co. Ltd.",     "verdigris.kr",          "KR"),
    ("Walnut Agency",       "contact@walnutagency.za",       "Walnut Agency (Pty)",    "walnutagency.za",       "ZA"),
    ("Xenon Partners",      "hello@xenonpartners.se",        "Xenon Partners AB",      "xenonpartners.se",      "SE"),
    ("Yucca Digital",       "info@yuccadigital.cl",          "Yucca Digital SpA",      "yuccadigital.cl",       "CL"),
    ("Zircon Group",        "team@zircongroup.ar",           "Zircon Group SA",        "zircongroup.ar",        "AR"),
    ("Ashwood Partners",    "contact@ashwoodpartners.gb",    "Ashwood Partners Ltd.",  "ashwoodpartners.co.uk", "GB"),
    ("Birch Digital",       "hello@birchdigital.pl",         "Birch Digital Sp.z.o.o.","birchdigital.pl",       "PL"),
    ("Cypress Ventures",    "info@cypressventures.gr",       "Cypress Ventures SA",    "cypressventures.gr",    "GR"),
    ("Driftwood Agency",    "team@driftwoodagency.cz",       "Driftwood Agency s.r.o.","driftwoodagency.cz",    "CZ"),
    ("Elmwood Consulting",  "contact@elmwoodconsulting.ro",  "Elmwood Consulting SRL", "elmwoodconsulting.ro",  "RO"),
    ("Fernwood Digital",    "hello@fernwooddigital.hu",      "Fernwood Digital Kft.",  "fernwooddigital.hu",    "HU"),
    ("Greystone",           "info@greystone.ch",             "Greystone AG",           "greystone.ch",          "CH"),
    ("Hazel Partners",      "team@hazelpartners.be",         "Hazel Partners BVBA",    "hazelpartners.be",      "BE"),
    ("Inkwood Group",       "contact@inkwoodgroup.ae",       "Inkwood Group FZE",      "inkwoodgroup.ae",       "AE"),
    ("Juniper Digital",     "hello@juniperdigital.dk",       "Juniper Digital ApS",    "juniperdigital.dk",     "DK"),
    ("Kestrel Partners",    "info@kestrelpartners.us",       "Kestrel Partners LLC",   "kestrelpartners.us",    "US"),
    ("Lynx Digital",        "hello@lynxdigital.ca",          "Lynx Digital Inc.",      "lynxdigital.ca",        "CA"),
    ("Merlin Consulting",   "team@merlinconsulting.gb",      "Merlin Consulting Ltd.", "merlinconsulting.co.uk","GB"),
]

REASONS = [
    "Expandir nuestra cartera con soluciones SaaS",
    "Generar ingresos recurrentes mediante referidos",
    "Acceder a nuevos mercados con apoyo de marca",
    "Complementar servicios existentes de consultoría",
    "Ofrecer valor añadido a nuestra base de clientes",
]

STATUSES = [
    PartnerStatus.Active,
    PartnerStatus.Active,
    PartnerStatus.Active,
    PartnerStatus.PendingReview,
    PartnerStatus.Suspended,
    PartnerStatus.Inactive,
    PartnerStatus.Rejected,
]


async def run():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with SessionLocal() as session:
        # Cargar sales reps existentes
        result = await session.execute(
            select(InternalUser).where(InternalUser.role == InternalRole.Sales)
        )
        sales_reps = result.scalars().all()

        if not sales_reps:
            print("ERROR: No hay usuarios con rol Sales en internal_users.")
            print("Ejecuta primero: .venv/bin/python seeds/internal_users.py")
            return

        print(f"Sales reps encontrados: {len(sales_reps)}")

        created = 0
        skipped = 0

        for name, email, company_name, website, country in PARTNERS_DATA:
            existing = await session.execute(
                select(Partner).where(Partner.email == email)
            )
            if existing.scalar_one_or_none():
                print(f"  omitido (ya existe): {email}")
                skipped += 1
                continue

            sales_rep = random.choice(sales_reps)
            status = random.choice(STATUSES)

            partner = Partner(
                name=name,
                email=email,
                password_hash=hash_password("Password1234!"),
                company_name=company_name,
                website=f"https://{website}",
                country=country,
                collaboration_reason=random.choice(REASONS),
                assigned_sales_rep_id=sales_rep.id,
                language_preference=random.choice(["en", "es", "fr", "de", "pt"]),
                referral_enabled=random.choice([True, False]),
                deals_enabled=random.choice([True, False]),
                status=status,
                self_billing_enabled=random.choice([True, False]),
            )
            session.add(partner)
            print(f"  creado: {email} [{status.value}] → sales: {sales_rep.name}")
            created += 1

        await session.commit()

    print(f"\nSeed completado: {created} creados, {skipped} omitidos.")


if __name__ == "__main__":
    asyncio.run(run())
