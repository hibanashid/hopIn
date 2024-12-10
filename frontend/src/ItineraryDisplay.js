import React from 'react';
import { Typography, Card, CardContent, List, ListItem, ListItemText, Divider } from '@mui/material';

function ItineraryDisplay({ itinerary }) {
  return (
    <div>
      <Typography variant="h4" component="h2" gutterBottom sx={{ mt: 4 }}>
        Your Itinerary
      </Typography>
      {Object.entries(itinerary.itinerary).map(([day, dayItinerary]) => (
        <Card key={day} sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h5" component="h3" gutterBottom>
              {day}
            </Typography>
            <List>
              {dayItinerary.activities.map((activity, index) => (
                <React.Fragment key={index}>
                  <ListItem alignItems="flex-start">
                    <ListItemText
                      primary={`${activity.time} - ${activity.activity}`}
                      secondary={
                        <>
                          <Typography component="span" variant="body2" color="text.primary">
                            {activity.place_name}
                          </Typography>
                          {` — ${activity.description}`}
                          {activity.rating && (
                            <Typography component="span" variant="body2" sx={{ display: 'block' }}>
                              Rating: {activity.rating}
                            </Typography>
                          )}
                          {activity.review && (
                            <Typography component="span" variant="body2" sx={{ display: 'block' }}>
                              Review: {activity.review}
                            </Typography>
                          )}
                          {activity.distance_to_next && (
                            <Typography component="span" variant="body2" sx={{ display: 'block' }}>
                              Distance to next: {activity.distance_to_next}
                            </Typography>
                          )}
                        </>
                      }
                    />
                  </ListItem>
                  {index < dayItinerary.activities.length - 1 && <Divider variant="inset" component="li" />}
                </React.Fragment>
              ))}
            </List>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

export default ItineraryDisplay;

