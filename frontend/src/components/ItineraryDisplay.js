import React from 'react';
import { useLocation } from 'react-router-dom';
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";

function ItineraryDisplay() {
  const location = useLocation();
  const { itinerary } = location.state;

  return (
    <div className="container mx-auto py-8">
      <h2 className="text-3xl font-bold mb-6 text-center">Your Itinerary</h2>
      <div className="space-y-4">
        {itinerary.map((day, index) => (
          <Card key={index} className="bg-gray-900">
            <CardHeader>
              <CardTitle className="text-yellow-400">Day {index + 1}</CardTitle>
            </CardHeader>
            <CardContent>
              <ul className="list-disc list-inside">
                {day[`Day ${index + 1}`].map((activity, actIndex) => (
                  <li key={actIndex} className="text-yellow-200">{activity}</li>
                ))}
              </ul>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}

export default ItineraryDisplay;

