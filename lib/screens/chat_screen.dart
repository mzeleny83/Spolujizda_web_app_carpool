import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'package:shared_preferences/shared_preferences.dart';

class ChatScreen extends StatefulWidget {
  const ChatScreen({super.key});

  @override
  State<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends State<ChatScreen> {
  final _messageController = TextEditingController();
  List<Map<String, dynamic>> _messages = [];
  int? _rideId;
  String? _partnerName;
  int? _currentUserId;

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    _initializeChat();
  }

  Future<void> _initializeChat() async {
    final args = ModalRoute.of(context)?.settings.arguments as Map<String, dynamic>?;
    _rideId = args?['ride_id'] ?? 1;
    _partnerName = args?['partner_name'] ?? 'Uživatel';
    
    final prefs = await SharedPreferences.getInstance();
    _currentUserId = prefs.getInt('user_id');
    
    await _loadMessages();
  }

  Future<void> _loadMessages() async {
    if (_rideId == null) return;
    
    try {
      final response = await http.get(
        Uri.parse('http://localhost:8081/api/rides/$_rideId/messages'),
      );
      
      if (response.statusCode == 200) {
        final messages = jsonDecode(response.body) as List;
        setState(() {
          _messages = messages.map((msg) => {
            'text': msg['message'],
            'isMe': msg['sender_id'] == _currentUserId,
            'time': DateTime.parse(msg['created_at']).toLocal().toString().substring(11, 16),
            'sender': msg['sender_name'],
          }).toList();
        });
      }
    } catch (e) {
      print('Chyba při načítání zpráv: $e');
    }
  }

  Future<void> _sendMessage() async {
    if (_messageController.text.isEmpty || _rideId == null || _currentUserId == null) return;
    
    final message = _messageController.text;
    _messageController.clear();
    
    try {
      final response = await http.post(
        Uri.parse('http://localhost:8081/api/messages/send'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'ride_id': _rideId,
          'sender_id': _currentUserId,
          'message': message,
        }),
      );
      
      if (response.statusCode == 201) {
        await _loadMessages();
        _sendPushNotification(message);
      }
    } catch (e) {
      print('Chyba při odesílání zprávy: $e');
    }
  }

  Future<void> _sendPushNotification(String message) async {
    try {
      await http.post(
        Uri.parse('http://localhost:8081/api/notifications/send'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'recipient': _partnerName,
          'title': 'Nová zpráva',
          'body': message,
          'type': 'chat_message',
        }),
      );
    } catch (e) {
      print('Chyba při odesílání notifikace: $e');
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Chat s ${_partnerName ?? "Uživatel"}'),
        actions: [
          IconButton(
            icon: const Icon(Icons.phone),
            onPressed: () {},
          ),
        ],
      ),
      body: Column(
        children: [
          Expanded(
            child: ListView.builder(
              itemCount: _messages.length,
              itemBuilder: (context, index) {
                final message = _messages[index];
                return Container(
                  margin: const EdgeInsets.symmetric(vertical: 4, horizontal: 8),
                  child: Row(
                    mainAxisAlignment: message['isMe'] 
                        ? MainAxisAlignment.end 
                        : MainAxisAlignment.start,
                    children: [
                      Container(
                        constraints: BoxConstraints(
                          maxWidth: MediaQuery.of(context).size.width * 0.7,
                        ),
                        padding: const EdgeInsets.all(12),
                        decoration: BoxDecoration(
                          color: message['isMe'] ? Colors.blue : Colors.grey[300],
                          borderRadius: BorderRadius.circular(16),
                        ),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              message['text'],
                              style: TextStyle(
                                color: message['isMe'] ? Colors.white : Colors.black,
                              ),
                            ),
                            const SizedBox(height: 4),
                            Text(
                              message['time'],
                              style: TextStyle(
                                fontSize: 12,
                                color: message['isMe'] 
                                    ? Colors.white70 
                                    : Colors.grey[600],
                              ),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                );
              },
            ),
          ),
          Container(
            padding: const EdgeInsets.all(8),
            child: Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _messageController,
                    decoration: const InputDecoration(
                      hintText: 'Napište zprávu...',
                      border: OutlineInputBorder(),
                    ),
                  ),
                ),
                const SizedBox(width: 8),
                IconButton(
                  onPressed: () => _sendMessage(),
                  icon: const Icon(Icons.send),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}