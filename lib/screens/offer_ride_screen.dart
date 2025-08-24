import 'package:flutter/material.dart';

class OfferRideScreen extends StatefulWidget {
  const OfferRideScreen({super.key});

  @override
  State<OfferRideScreen> createState() => _OfferRideScreenState();
}

class _OfferRideScreenState extends State<OfferRideScreen> {
  final _fromController = TextEditingController();
  final _toController = TextEditingController();
  final _timeController = TextEditingController();
  final _seatsController = TextEditingController();
  final _priceController = TextEditingController();

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Nabídnout jízdu')),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: SingleChildScrollView(
          child: Column(
            children: [
              TextFormField(
                controller: _fromController,
                decoration: const InputDecoration(
                  labelText: 'Odkud',
                  hintText: 'Zadejte výchozí místo',
                  border: OutlineInputBorder(),
                  prefixIcon: Icon(Icons.location_on),
                ),
              ),
              const SizedBox(height: 16),
              TextFormField(
                controller: _toController,
                decoration: const InputDecoration(
                  labelText: 'Kam',
                  hintText: 'Zadejte cílové místo',
                  border: OutlineInputBorder(),
                  prefixIcon: Icon(Icons.flag),
                ),
              ),
              const SizedBox(height: 16),
              TextFormField(
                controller: _timeController,
                decoration: const InputDecoration(
                  labelText: 'Čas odjezdu',
                  border: OutlineInputBorder(),
                  prefixIcon: Icon(Icons.access_time),
                ),
                onTap: () async {
                  final time = await showTimePicker(
                    context: context,
                    initialTime: TimeOfDay.now(),
                  );
                  if (time != null) {
                    _timeController.text = time.format(context);
                  }
                },
              ),
              const SizedBox(height: 16),
              TextFormField(
                controller: _seatsController,
                decoration: const InputDecoration(
                  labelText: 'Počet míst',
                  border: OutlineInputBorder(),
                  prefixIcon: Icon(Icons.airline_seat_recline_normal),
                ),
                keyboardType: TextInputType.number,
              ),
              const SizedBox(height: 16),
              TextFormField(
                controller: _priceController,
                decoration: const InputDecoration(
                  labelText: 'Cena za osobu (Kč)',
                  hintText: 'Zadejte cenu',
                  border: OutlineInputBorder(),
                  prefixIcon: Icon(Icons.attach_money),
                ),
                keyboardType: TextInputType.number,
              ),
              const SizedBox(height: 32),
              SizedBox(
                width: double.infinity,
                child: ElevatedButton(
                  onPressed: () {
                    ScaffoldMessenger.of(context).showSnackBar(
                      const SnackBar(content: Text('Jízda byla nabídnuta!')),
                    );
                    Navigator.pop(context);
                  },
                  child: const Text('Nabídnout jízdu'),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}