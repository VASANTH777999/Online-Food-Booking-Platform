const admin = require("firebase-admin");
const dotenv = require("dotenv");
const path = require("path");

dotenv.config();

// Load Firebase credentials
const serviceAccount = require(path.join(__dirname, "firebase-adminsdk.json"));

admin.initializeApp({
  credential: admin.credential.cert(serviceAccount),
});

console.log("🔥 Firebase Initialized Successfully!");

module.exports = admin;
