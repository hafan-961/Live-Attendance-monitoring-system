from pymongo import MongoClient

#mongodb must be installed and running on your computer.
client = MongoClient(
    "mongodb://localhost:27017/",
    serverSelectionTimeoutMS=5000,
)

client.admin.command("ping")  #verify connection

db = client["live_attendance"]
students_collection = db["students"]

#save or update one student without creating duplicates.
students_collection.update_one(
    {"reg_no": "DEMO001"},
    {"$set": {"name": "Demo Student", "section": "A"}},
    upsert=True,
)

print("Student saved to MongoDB")
client.close()
