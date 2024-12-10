import React, { useState } from 'react';
import { useHistory } from 'react-router-dom';
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";

function ItineraryForm() {
  const [destination, setDestination] = useState('');
  const [numDays, setNumDays] = useState('');
  const history = useHistory();

  const handleSubmit = async (e) => {
    e.preventDefault();
    // Implement itinerary generation logic here
    // On success, redirect to ItineraryDisplay with the generated itinerary
    history.push('/itinerary', { itinerary: generatedItinerary });
  };

  return (
    <div className="flex items-center justify-center min-h-screen">
      <div className="w-full max-w-md">
        <h2 className="text-3xl font-bold mb-6 text-center">Generate Itinerary</h2>
        <form onSubmit={handleSubmit} className="space-y-4">
          <Input
            type="text"
            placeholder="Destination"
            value={destination}
            onChange={(e) => setDestination(e.target.value)}
            required
          />
          <Input
            type="number"
            placeholder="Number of Days"
            value={numDays}
            onChange={(e) => setNumDays(e.target.value)}
            required
            min="1"
          />
          <Button type="submit" className="w-full">Generate Itinerary</Button>
        </form>
      </div>
    </div>
  );
}

export default ItineraryForm;

