import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'package:shared_preferences/shared_preferences.dart';

class RatingScreen extends StatefulWidget {
  const RatingScreen({super.key});

  @override
  State<RatingScreen> createState() => _RatingScreenState();
}

class _RatingScreenState extends State<RatingScreen> {
  int _rating = 5;
  final _commentController = TextEditingController();
  bool _isLoading = false;

  Future<void> _submitRating() async {
    final args = ModalRoute.of(context)!.settings.arguments as Map<String, dynamic>;
    final rideId = args['ride_id'];
    final ratedUserId = args['rated_user_id'];
    final ratedUserName = args['rated_user_name'];
    
    setState(() => _isLoading = true);
    
    try {
      final prefs = await SharedPreferences.getInstance();
      final raterId = prefs.getInt('user_id');
      
      final response = await http.post(
        Uri.parse('http://localhost:8081/api/ratings/create'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'ride_id': rideId,
          'rater_id': raterId,
          'rated_id': ratedUserId,
          'rating': _rating,
          'comment': _commentController.text.trim(),
        }),
      );
      
      if (response.statusCode == 201) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Hodnocení odesláno!')),
        );
        Navigator.pop(context);
      } else {
        final data = jsonDecode(response.body);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(data['error'] ?? 'Chyba při odesílání')),
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

  Widget _buildStarRating() {
    return Column(
      children: [
        Text(
          'Hodnocení: $_rating/5',
          style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
        ),
        const SizedBox(height: 16),
        Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: List.generate(5, (index) {
            return Padding(
              padding: const EdgeInsets.symmetric(horizontal: 4),
              child: GestureDetector(
                onTap: () => setState(() => _rating = index + 1),
                child: Container(
                  padding: const EdgeInsets.all(8),
                  decoration: BoxDecoration(
                    color: index < _rating ? Colors.amber.shade100 : Colors.transparent,
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Icon(
                    index < _rating ? Icons.star : Icons.star_border,
                    color: index < _rating ? Colors.amber.shade700 : Colors.grey,
                    size: 48,
                  ),
                ),
              ),
            );
          }),
        ),
      ],
    );
  }

  @override
  Widget build(BuildContext context) {
    final args = ModalRoute.of(context)!.settings.arguments as Map<String, dynamic>;
    final ratedUserName = args['rated_user_name'] ?? 'Uživatel';
    
    return Scaffold(
      appBar: AppBar(title: const Text('Hodnocení')),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          children: [
            Text(
              'Ohodnoťte uživatele: $ratedUserName',
              style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 32),
            _buildStarRating(),
            const SizedBox(height: 32),
            TextField(
              controller: _commentController,
              decoration: const InputDecoration(
                labelText: 'Komentář (volitelný)',
                border: OutlineInputBorder(),
              ),
              maxLines: 3,
            ),
            const SizedBox(height: 32),
            SizedBox(
              width: double.infinity,
              child: ElevatedButton(
                onPressed: _isLoading ? null : _submitRating,
                child: _isLoading 
                  ? const CircularProgressIndicator()
                  : const Text('Odeslat hodnocení'),
              ),
            ),
          ],
        ),
      ),
    );
  }
}