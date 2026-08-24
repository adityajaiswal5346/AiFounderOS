import asyncio
from db.connection import get_db
from db.repository import approval_repository

async def main():
    async with get_db() as db:
        pending = await approval_repository.get_pending_approvals(db)
        if not pending:
            print("No pending approvals.")
        else:
            for a in pending:
                print(f"\nApproval ID: {a.id}")
                print(f"Action: {a.tool_name}")
                print(f"Payload: {a.payload}")
                decision = input("Approve? (y/n): ").strip().lower()
                await approval_repository.resolve_approval(db, a.id, approved=(decision == "y"))

if __name__ == "__main__":
    asyncio.run(main())