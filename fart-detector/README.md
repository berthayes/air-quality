## Fart Detector
Sending air-quality metrics to the Cloud is fun and all but what can you make from it? A hat? A broach? A pterydactyl?

How about a fart detector? 

While working on early prototypes, I discovered a handful of spikes in TVOC and CO2 concentration when the device was left to run overnight in my home-office. It wasn't until the next day, while collaborating with the cutest girl in the office (our dog) that she let me know that she was the source of the spikes. It was then that I realized that if I had not built an air-quality monitor, I had built an IoT Fart Detector.

To detect and alert on sudden spikes in CO2 and TVOC concentration, use the included `fart-detector.json` pipeline in Cribl Cloud. This calls a chained function, `ntfy_postprocessing.json` for processing the event for the [NTFY.sh](https://ntfy.sh) notification service.

### The pipeline
The pipeline for analyzing air quality and sending alerts does the following:
- Clean up the incoming data for easier processing
    - Parse the data from _raw into a JSON object so individual fields can be processed
    - Flatten the nested JSON field data so that all information is now in one JSON object without nesting
    - Rename the flattened data fields, e.g. data_CO2 becomes co2_ppm
    - Drop a bunch of fields we no longer need
- Process the data with Redis
    - Take the latest reading and push it to a Redis database
    - Retrieve the last 10 readings as an array
    - Use the Numerify function to ensure we’re working with numbers not strings
    - Flatten the array
    - Take those 10 readings and calculate the average value and standard deviation
    - Serialize the 10 readings into a hidden JSON object just to clean things up
    - Add a “timestamp” field to the object from _time
    - Drop some fields we no longer need and clean up a few others
    - If the last CO2 reading is more than 3 standard deviations away from the last 10 readings (and the value is over 1000) then you’ve got a spike! Add the field toots and give it the value totes! `toots = "totes"`
    - Serialize fields worth reporting into JSON into the field message.
    - Remove some fields that are no longer needed.
    - Since we’re using this pipeline to alert on spikes in values, we don’t care about events without “toots: totes”, so we drop them.
- Now we're ready for the `ntfy_postprocessing.json` pipeline
    - Rename the `_raw` field as `message`
    - Add a topic and title field to the JSON object to send

The NTFY destination in Cribl Stream is a Webhook and is about as [easy as it gets](https://docs.ntfy.sh/publish/#publish-as-json) when it comes to sending notifications.
