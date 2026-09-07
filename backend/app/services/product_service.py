import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.product import Product
from app.services.plan_limit_service import check_product_limit


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
    retailer_id: Optional[uuid.UUID] = None,
) -> Optional[Product]:
    statement = select(Product).where(
        Product.product_code == product_code
    )

    if retailer_id is not None:
        statement = statement.where(
            Product.retailer_id == retailer_id
        )

    return db.execute(
        statement
    ).scalar_one_or_none()


def get_all_products(
    db: Session,
    retailer_id: Optional[uuid.UUID] = None,
) -> list[Product]:
    statement = select(Product)

    if retailer_id is not None:
        statement = statement.where(
            Product.retailer_id == retailer_id
        )

    statement = statement.order_by(
        Product.created_at.desc()
    )

    return list(
        db.execute(statement).scalars().all()
    )


def create_product(
    db: Session,
    retailer_id: uuid.UUID,
    name: str,
    product_code: Optional[str] = None,
    brand: Optional[str] = None,
    category: Optional[str] = None,
    description: Optional[str] = None,
    is_transferable: bool = True,
) -> Product:

    check_product_limit(
        db,
        retailer_id,
    )

    if product_code:
        existing_product = get_product_by_code(
            db,
            product_code,
            retailer_id=retailer_id,
        )

        if existing_product:
            raise ValueError(
                "A product with this product code already exists."
            )
    else:
        product_code = generate_product_code()

    product = Product(
        retailer_id=retailer_id,
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