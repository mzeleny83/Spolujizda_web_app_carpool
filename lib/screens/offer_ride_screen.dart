import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'package:shared_preferences/shared_preferences.dart';

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
  bool _isLoading = false;

  Future<void> _offerRide() async {
    if (_fromController.text.isEmpty || _toController.text.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Vyplňte všechna povinná pole')),
      );
      return;
    }

    setState(() => _isLoading = true);

    try {
      final prefs = await SharedPreferences.getInstance();
      final userId = prefs.getInt('user_id');

      final response = await http.post(
        Uri.parse('https://spolujizda-645ec54e47aa.herokuapp.com/api/rides/offer'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'driver_id': userId,
          'from_location': _fromController.text.trim(),
          'to_location': _toController.text.trim(),
          'departure_time': DateTime.now().add(Duration(hours: 1)).toIso8601String(),
          'available_seats': int.tryParse(_seatsController.text) ?? 1,
          'price': double.tryParse(_priceController.text) ?? 0.0,
          'description': 'Jízda nabídnuta přes mobilní aplikaci'
        }),
      );

      if (response.statusCode == 201) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Jízda byla úspěšně nabídnuta!')),
        );
        Navigator.pop(context);
      } else {
        final data = jsonDecode(response.body);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(data['error'] ?? 'Chyba při nabídce jízdy')),
        );
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Chyba připojení: $e')),
      );
    } finally {
      setState(() => _isLoading = false);
    }
  }

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
                  onPressed: _isLoading ? null : _offerRide,
                  child: _isLoading 
                    ? const CircularProgressIndicator()
                    : const Text('Nabídnout jízdu'),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}