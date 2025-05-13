const express = require('express');
const path = require('path');
const app = express();
const PORT = 3000;

// Serve static files (if you have HTML, CSS, or JS files)
app.use(express.static(path.join(__dirname, 'public')));

// Route for the homepage
app.get('/', (req, res) => {
  res.send('<h1>Hello from Maxx Mai Card Assignment!</h1>');
});

// Route for the game page
app.get('/game', (req, res) => {
  res.send('<h1>Welcome to the card game!</h1>');
});

// Start the server
app.listen(PORT, () => {
  console.log(`Server is running on http://localhost:${PORT}`);
});
