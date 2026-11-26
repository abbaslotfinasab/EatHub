from accounts.services.business_service import BusinessService


class AuthService:
    @staticmethod
    def create_first_business(user, name: str):
        return BusinessService.create_business(user=user, name=name)
