from access_service.domain.models import Base
from access_service.infrastructure.database import engine


def main() -> None:
    Base.metadata.create_all(engine)
    print("Access Service schema is ready")


if __name__ == "__main__":
    main()

