from email_validator import validate_email, EmailNotValidError
for e in ['test@example.com','t@example.com','invalid@']:
    try:
        v = validate_email(e)
        print(e, 'valid ->', v.email)
    except EmailNotValidError as ex:
        print(e, 'invalid ->', str(ex))
