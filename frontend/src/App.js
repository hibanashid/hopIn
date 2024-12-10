import React, { useState } from 'react';
import { Container, Typography, TextField, Button, Box, CircularProgress } from '@mui/material';
import ItineraryDisplay from './ItineraryDisplay';
import axios from 'axios';

function App() {
  const [destination, setDestination] = useState('');
  const [days, setDays] = useState(1);
  const [foodPreference, setFoodPreference] = useState('');
  const [itinerary, setItinerary] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const response = await axios.get(`/generate_itinerary/`, {
        params: {
          destination,
          no_of_days: days,
          food_preference: foodPreference
        }
      });
      setItinerary(response.data);
    } catch (err) {
      setError('Failed to generate itinerary. Please try again.');
      console.error(err);
    }
    setLoading(false);
  };

  return (
    <Container maxWidth="md">
      <Typography variant="h2" component="h1" gutterBottom>
        Travel Itinerary Generator
      </Typography>
      <Box component="form" onSubmit={handleSubmit} sx={{ mt: 3 }}>
        <TextField
          fullWidth
          label="Destination"
          value={destination}
          onChange={(e) => setDestination(e.target.value)}
          margin="normal"
          required
        />
        <TextField
          fullWidth
          label="Number of Days"
          type="number"
          value={days}
          onChange={(e) => setDays(e.target.value)}
          margin="normal"
          required
          InputProps={{ inputProps: { min: 1 } }}
        />
        <TextField
          fullWidth
          label="Food Preference"
          value={foodPreference}
          onChange={(e) => setFoodPreference(e.target.value)}
          margin="normal"
        />
        <Button
          type="submit"
          variant="contained"
          color="primary"
          size="large"
          sx={{ mt: 2 }}
          disabled={loading}
        >
          Generate Itinerary
        </Button>
      </Box>
      {loading && (
        <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
          <CircularProgress />
        </Box>
      )}
      {error && (
        <Typography color="error" sx={{ mt: 2 }}>
          {error}
        </Typography>
      )}
      {itinerary && <ItineraryDisplay itinerary={itinerary} />}
    </Container>
  );
}

export default App;
