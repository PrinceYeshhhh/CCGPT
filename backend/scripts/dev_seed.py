import json
from app.core.database import db_manager
from app.services.user import UserService
from app.schemas.user import UserCreate
from app.services.auth import AuthService
from app.services.embed_service import EmbedService


def main() -> None:
    db = db_manager.get_write_session()
    try:
        user_service = UserService(db)
        auth_service = AuthService(db)

        email = "owner@example.com"
        password = "Passw0rd!"

        user = user_service.get_user_by_email(email)
        if not user:
            user = user_service.create_user(
                UserCreate(
                    email=email,
                    password=password,
                    full_name="Owner User",
                    business_name="OwnerCo",
                    business_domain="owner.example.com",
                ),
                mobile_phone="+10000000000",
                phone_verified=True,
            )
            # Mark email verified
            user.email_verified = True
            db.commit()
            db.refresh(user)

        # Issue tokens
        access_token = auth_service.create_access_token(data={"sub": user.email})
        refresh_token = auth_service.create_refresh_token(data={"sub": user.email})

        # Ensure embed code exists
        embed_service = EmbedService(db)
        existing_codes = embed_service.get_user_embed_codes(user.id)
        if existing_codes:
            embed_code = existing_codes[0]
        else:
            embed_code = embed_service.generate_embed_code(
                workspace_id=str(user.workspace_id),
                user_id=user.id,
                code_name="dev",
                config=None,
                snippet_template=None,
            )

        output = {
            "user_id": user.id,
            "workspace_id": str(user.workspace_id),
            "access_token": access_token,
            "refresh_token": refresh_token,
            "embed_code_id": str(embed_code.id),
            "client_api_key": embed_code.client_api_key,
        }
        print(json.dumps(output))
    finally:
        db.close()


if __name__ == "__main__":
    main()


