import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.product import Product


def generate_product_code() -> str:
    return f"PROD-{uuid.uuid4().hex[:10].upper()}"


def get_product_by_id(
    db: Session,
    product_id: uuid.UUID,
) -> Optional[Product]:
    statement = select(Product).where(
        Product.id == product_id
    )

    return db.execute(
        statement
    ).scalar_one_or_none()


def get_product_by_code(
    db: Session,
    product_code: str,
) -> Optional[Product]:
    statement = select(Product).where(
        Product.product_code == product_code
    )

    return db.execute(
        statement
    ).scalar_one_or_none()


def create_product(
    db: Session,
    name: str,
    product_code: Optional[str] = None,
    brand: Optional[str] = None,
    category: Optional[str] = None,
    description: Optional[str] = None,
    is_transferable: bool = True,
) -> Product:

    if product_code:
        existing_product = get_product_by_code(
            db,
            product_code,
        )

        if existing_product:
            raise ValueError(
                "A product with this product code already exists."
            )
    else:
        product_code = generate_product_code()

    product = Product(
        product_code=product_code,
        name=name,
        brand=brand,
        category=category,
        description=description,
        is_transferable=is_transferable,
        status="active",
    )

    db.add(product)
    db.commit()
    db.refresh(product)

    return product