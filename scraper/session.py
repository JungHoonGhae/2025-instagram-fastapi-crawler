import asyncio
import json

from fastapi import HTTPException
from instagrapi import Client
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models import InstagramSession


async def insta_create_session(data, db: AsyncSession):
    # Create a new client instance
    cl = Client()
    proxy_ip="http://170.64.207.199"
    proxy_port="22"
    set_proxy = f"{proxy_ip}:{proxy_port}"
    cl.set_proxy(set_proxy)

    try:
        # Log in to the account using Executor to avoid blocking
        await asyncio.get_event_loop().run_in_executor(
            None, lambda: cl.login(data.username, data.password)
        )

        # Retrieve the current session and save it
        session_data = await asyncio.get_event_loop().run_in_executor(
            None, cl.get_settings
        )

        try:
            # Convert session_data to JSON and then to a dictionary
            session_data = json.loads(json.dumps(session_data))
        except Exception as e:
            # Raise an HTTPException if serialization fails
            raise HTTPException(
                status_code=500, detail=f"Session data serialization failed: {str(e)}"
            )

        # Save settings to a JSON file
        print("Session OK")

        # Check if a profile already exists for the user
        profile = (
            db.query(InstagramSession)
            .filter(InstagramSession.username == data.username)
            .first()
        )

        if profile:
            # Update the existing profile with the new session data
            profile.password = data.password  # Update password if needed
            profile.session_data = session_data
            print(f"Profile {data.username} updated with new session data.")
        else:
            # Create a new profile entry in the database
            new_profile = InstagramSession(
                username=data.username,
                password=data.password,
                session_data=session_data,
            )
            db.add(new_profile)
            db.commit()
            db.refresh(new_profile)
            profile = new_profile

        return {
            "profile": profile,
            "status": "success",
            "message": "Session created/updated and saved successfully!",
            "session_data": session_data,
        }

    except Exception as e:
        # Raise an HTTPException for any other errors
        raise HTTPException(
            status_code=400, detail={"status": "error", "message": str(e)}
        )


async def save_session(data, db: AsyncSession):
    """
    Saves or updates an Instagram session in the database.

    Args:
        data: An object containing the session data (username, password, session_data).
        db: An asynchronous session instance for database operations.

    Returns:
        A dictionary with a success or error message along with the username.
    """

    # Prepare a SQL query to check if an InstagramSession with the provided username already exists.
    stmt = select(InstagramSession).where(InstagramSession.username == data.username)
    result = db.execute(stmt)  # Execute the query.
    session = (
        result.scalars().first()
    )  # Fetch the first result as an InstagramSession object.

    if session:  # If a session with the username already exists.

        try:
            # Update the existing session's data.
            session.session_data = data.session_data
            db.add(session)  # Add the updated session to the database.
            db.commit()  # Commit the changes to the database.
            db.refresh(session)  # Refresh the session object with the new data.

            # Return a success message along with the updated username.
            return {
                "message": "JSON data updated successfully",
                "updated_data": data.username,
            }
        except Exception as e:
            # If there is an exception, return an error message and the username.
            return {"message": str(e), "username": data.username}

    else:  # If no session with the username exists.

        try:
            # Create a new Instagram session with the provided data.
            new_session = InstagramSession(
                username=data.username,
                password=data.password,
                session_data=data.session_data,
            )
            db.add(new_session)  # Add the new session to the database.
            db.commit()  # Commit the new session to the database.
            db.refresh(new_session)  # Refresh the session object with the new data.

            # Return a success message along with the new session's username.
            return {
                "message": "User created and JSON data added successfully",
                "username": new_session.username,
            }
        except Exception as e:
            # If there is an exception, return an error message and the username.
            return {"message": str(e), "username": data.username}
