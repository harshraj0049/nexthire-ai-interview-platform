from ..models.user import User
def get_user_by_email(db, email):
    return db.query(User).filter(User.email == email).first()


def get_user_by_phone(db, phone):
    return db.query(User).filter(User.phone_no == phone).first()


def create_user(db, name, email, hashed, phone):
    user = User(
        name=name,
        email=email,
        password_hashed=hashed,
        phone_no=phone,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def get_user_by_id(db,user_id):
    return db.query(User).filter(User.user_id==user_id).first()
