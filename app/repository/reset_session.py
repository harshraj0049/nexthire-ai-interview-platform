from ..models.password_reset import PasswordResetSession

def create_password_reset_session_in_db(db,user_id,hashed_otp,otp_expiry):
    reset_session=PasswordResetSession(
        user_id=user_id,
        otp=hashed_otp,
        otp_expiry=otp_expiry
    )
    db.add(reset_session)
    db.commit()
    db.refresh(reset_session)
    return reset_session

def get_reset_session_by_token(db, token):
    return db.query(PasswordResetSession).filter(PasswordResetSession.session_id == token).first()

def increment_reset_attempts(db, session_id):
    session = db.query(PasswordResetSession).filter(PasswordResetSession.session_id == session_id).first()
    if session:
        session.reset_attempts += 1
        db.commit()

def reset_session_verified(db, session_id):
    session = db.query(PasswordResetSession).filter(PasswordResetSession.session_id == session_id).first()
    if session:
        session.verified = True
        db.commit()

def reset_session_delete(db, session_id):
    session = db.query(PasswordResetSession).filter(PasswordResetSession.session_id == session_id).first()
    if session:
        db.delete(session)
        db.commit()