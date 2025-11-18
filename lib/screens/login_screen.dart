import 'package:flutter/material.dart';
import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _formKey = GlobalKey<FormState>();
  final _phoneController = TextEditingController(text: '721745084'); // Pre-fill test phone
  final _passwordController = TextEditingController(text: '123'); // Pre-fill test password
  bool _isLoading = false;
  bool _obscurePassword = true;

  Future<void> _login() async {
    if (!_formKey.currentState!.validate()) return;
    
    setState(() => _isLoading = true);
    
    try {
      final response = await http.post(
        Uri.parse('https://spolujizda-645ec54e47aa.herokuapp.com/api/users/login'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'phone': _phoneController.text.trim(),
          'password': _passwordController.text,
        }),
      );
      
      final data = jsonDecode(response.body);
      
      if (response.statusCode == 200) {
        // Uloží uživatelské údaje
        final prefs = await SharedPreferences.getInstance();
        await prefs.setInt('user_id', data['user_id']);
        await prefs.setString('user_name', data['name']);
        await prefs.setDouble('user_rating', (data['rating'] ?? 5.0).toDouble());
        
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Přihlášení úspěšné!')),
        );
        Navigator.pushReplacementNamed(context, '/home');
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(data['error'] ?? 'Neplatné přihlašovací údaje')),
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
      appBar: AppBar(title: const Text('Přihlášení')),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Form(
          key: _formKey,
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Text('Spolujízda', style: TextStyle(fontSize: 32, fontWeight: FontWeight.bold)),
              const SizedBox(height: 40),
              TextFormField(
                controller: _phoneController,
                decoration: const InputDecoration(
                  labelText: 'Telefon nebo Email', 
                  border: OutlineInputBorder(),
                  hintText: '721745084 (testovací účet)'
                ),
                validator: (value) => value?.isEmpty == true ? 'Telefon nebo email je povinný' : null,
              ),
              const SizedBox(height: 16),
              TextFormField(
                controller: _passwordController,
                decoration: InputDecoration(
                  labelText: 'Heslo',
                  border: const OutlineInputBorder(),
                  hintText: '123, password, admin, nebo heslo',
                  suffixIcon: IconButton(
                    icon: Icon(_obscurePassword ? Icons.visibility : Icons.visibility_off),
                    onPressed: () => setState(() => _obscurePassword = !_obscurePassword),
                  ),
                ),
                obscureText: _obscurePassword,
                validator: (value) => value?.isEmpty == true ? 'Heslo je povinné' : null,
              ),
              const SizedBox(height: 24),
              SizedBox(
                width: double.infinity,
                child: ElevatedButton(
                  onPressed: _isLoading ? null : _login,
                  child: _isLoading 
                    ? const CircularProgressIndicator()
                    : const Text('Přihlásit se'),
                ),
              ),
              TextButton(
                onPressed: () => Navigator.pushNamed(context, '/register'),
                child: const Text('Registrovat se'),
              ),
            ],
          ),
        ),
      ),
    );
  }
}