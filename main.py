from flask import Flask, jsonify, request
from pymongo import MongoClient

# Initialize Flask app
app = Flask(__name__)

# MongoDB connection
client = MongoClient("mongodb+srv://admin:123@cluster0.cz2uq.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
db = client["API"]  
blocks_collection = db["Blockchain"]  

# Welcome Route
@app.route("/")
def index():
    return jsonify({"message": "Welcome to the Bitcoin Blockchain REST API!"})

# Endpoint: Get a block by height
@app.route("/blocks/<int:height>", methods=["GET"])
def get_block_by_height(height):
    block = blocks_collection.find_one({"height": height})
    if block:
        block["_id"] = str(block["_id"])  # Convert ObjectId to string for JSON
        return jsonify(block)
    else:
        return jsonify({"error": "Block not found"}), 404

# Endpoint: Get all blocks (paginated)
@app.route("/blocks", methods=["GET"])
def get_all_blocks():
    # Pagination parameters
    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 10))

    # Calculate skip and limit
    skip = (page - 1) * per_page
    cursor = blocks_collection.find().skip(skip).limit(per_page)

    # Prepare results
    blocks = []
    for block in cursor:
        block["_id"] = str(block["_id"])  # Convert ObjectId to string
        blocks.append(block)

    return jsonify(blocks)

# Endpoint: Get blocks within a height range
@app.route("/blocks/range", methods=["GET"])
def get_blocks_by_range():
    start_height = int(request.args.get("start", 0))
    end_height = int(request.args.get("end", 10))

    cursor = blocks_collection.find({"height": {"$gte": start_height, "$lte": end_height}})
    blocks = []
    for block in cursor:
        block["_id"] = str(block["_id"])  # Convert ObjectId to string
        blocks.append(block)

    return jsonify(blocks)

# Endpoint: Search blocks by hash
@app.route("/blocks/hash/<string:block_hash>", methods=["GET"])
def get_block_by_hash(block_hash):
    block = blocks_collection.find_one({"hash": block_hash})
    if block:
        block["_id"] = str(block["_id"])  # Convert ObjectId to string
        return jsonify(block)
    else:
        return jsonify({"error": "Block not found"}), 404

# Endpoint: Add a new block
@app.route("/blocks", methods=["POST"])
def add_block():
    block_data = request.json
    if not block_data:
        return jsonify({"error": "Invalid request. No JSON data provided."}), 400

    try:
        # Insert the block into the collection
        result = blocks_collection.insert_one(block_data)
        return jsonify({"message": "Block added", "block_id": str(result.inserted_id)}), 201
    except Exception as e:
        return jsonify({"error": f"Failed to add block. {e}"}), 500

# Endpoint: Get transaction by hash
@app.route("/blocks/transaction/<string:tx_hash>", methods=["GET"])
def get_transaction_by_hash(tx_hash):
    block = blocks_collection.find_one({"tx.hash": tx_hash})
    if block:
        # Find the transaction in the block
        transaction = next((tx for tx in block["tx"] if tx["hash"] == tx_hash), None)
        if transaction:
            return jsonify(transaction)
        else:
            return jsonify({"error": "Transaction not found in block"}), 404
    else:
        return jsonify({"error": "Block not found"}), 404
    
# Endpoint: Update block by height
@app.route("/blocks/<int:height>", methods=["PUT"])
def update_block(height):
    block_data = request.json
    if not block_data:
        return jsonify({"error": "Invalid request. No JSON data provided."}), 400

    updated_block = blocks_collection.find_one_and_update(
        {"height": height},
        {"$set": block_data},
        return_document=True
    )

    if updated_block:
        updated_block["_id"] = str(updated_block["_id"])  # Convert ObjectId to string
        return jsonify(updated_block)
    else:
        return jsonify({"error": "Block not found"}), 404

# Endpoint: Delete a block by height
@app.route("/blocks/<int:height>", methods=["DELETE"])
def delete_block(height):
    result = blocks_collection.delete_one({"height": height})

    if result.deleted_count > 0:
        return jsonify({"message": "Block deleted successfully"})
    else:
        return jsonify({"error": "Block not found"}), 404

# Endpoint: Get the latest block
@app.route("/blocks/latest", methods=["GET"])
def get_latest_block():
    block = blocks_collection.find().sort("height", -1).limit(1)
    latest_block = block[0] if block.count() > 0 else None
    if latest_block:
        latest_block["_id"] = str(latest_block["_id"])
        return jsonify(latest_block)
    else:
        return jsonify({"error": "No blocks found"}), 404

# Endpoint: Get all transactions in a block by height
@app.route("/blocks/<int:height>/transactions", methods=["GET"])
def get_transactions_in_block(height):
    block = blocks_collection.find_one({"height": height})
    if block:
        transactions = block["tx"]
        return jsonify(transactions)
    else:
        return jsonify({"error": "Block not found"}), 404


# Run the Flask app
if __name__ == "__main__":
    app.run(debug=True)
