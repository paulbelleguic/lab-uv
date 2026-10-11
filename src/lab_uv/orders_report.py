import argparse
import os

import duckdb


def orders_report(product=None):
    con = duckdb.connect()
    con.execute("SET TimeZone = 'UTC'")

    # Configuration de l'accès au bucket S3
    con.execute("INSTALL aws")
    con.execute("LOAD aws")

    con.execute("""
        CREATE OR REPLACE SECRET s3_onyxia_connection (
            TYPE s3,
            PROVIDER credential_chain,
            CHAIN config,
            PROFILE 'default',
            REGION 'us-east-1',
            ENDPOINT 's3.seaweedfs.adm.adaltas.cloud',
            URL_STYLE 'path',
            USE_SSL true
        )
    """)

    # Emplacement des données
    bronze = f"s3://{os.environ['LAB_BUCKET_NAME']}/bronze"

    # Calcul du rapport mensuel
    return con.execute(
        f"""
        SELECT strftime(date, '%Y-%m') AS month,
               count(*) AS orders,
               sum(quantity) AS quantity
        FROM read_csv('{bronze}/orders.csv', strict_mode = false)
        WHERE $product IS NULL OR product = $product
        GROUP BY month
        ORDER BY month
        """,
        {"product": product},
    ).fetchall()


def main():
    parser = argparse.ArgumentParser(
        prog="orders-report",
        description="Monthly orders report",
    )
    parser.add_argument("-p", "--product", help="Filter the orders on a product.")
    args = parser.parse_args()

    for month, orders, quantity in orders_report(args.product):
        print(f"{month}\t{orders}\t{quantity}")


if __name__ == "__main__":
    main()

