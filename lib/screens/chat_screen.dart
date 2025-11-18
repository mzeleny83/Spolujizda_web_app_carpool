import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';

class ChatScreen extends StatefulWidget {
  const ChatScreen({super.key});

  @override
  State<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends State<ChatScreen> {
  final _messageController = TextEditingController();
  String? _contactName;
  String? _contactPhone;
  String? _rideInfo;
  List<Map<String, String>> _messages = [];

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    final arguments = ModalRoute.of(context)?.settings.arguments;
    if (arguments != null && arguments is Map<String, dynamic>) {
      _contactName = arguments['contact_name']?.toString();
      _contactPhone = arguments['contact_phone']?.toString();
      _rideInfo = arguments['ride_info']?.toString();
      
      // Inicializace zpráv s kontextem jízdy
      if (_messages.isEmpty) {
        _messages = [
          {'sender': _contactName ?? 'Kontakt', 'message': 'Ahoj! Vidím, že máte zájem o jízdu $_rideInfo', 'time': '14:30'},
          {'sender': 'Já', 'message': 'Ano, rád bych si zarezervoval místo', 'time': '14:32'},
          {'sender': _contactName ?? 'Kontakt', 'message': 'Výborně! Kde se sejdeme?', 'time': '14:35'},
        ];
      }
    } else {
      // Fallback pro případ, kdy nejsou argumenty
      _contactName = 'Kontakt';
      _contactPhone = '+420721745084';
      _rideInfo = 'Jízda';
      if (_messages.isEmpty) {
        _messages = [
          {'sender': 'Kontakt', 'message': 'Ahoj! Jak se máte?', 'time': '14:30'},
        ];
      }
    }
  }

  Future<void> _makePhoneCall() async {
    if (_contactPhone != null) {
      final Uri phoneUri = Uri(scheme: 'tel', path: _contactPhone);
      try {
        if (await canLaunchUrl(phoneUri)) {
          await launchUrl(phoneUri);
        } else {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text('Nelze volat na číslo $_contactPhone')),
          );
        }
      } catch (e) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Chyba při volání: $e')),
        );
      }
    }
  }

  Future<void> _sendSMS() async {
    if (_contactPhone != null) {
      final Uri smsUri = Uri(scheme: 'sms', path: _contactPhone);
      try {
        if (await canLaunchUrl(smsUri)) {
          await launchUrl(smsUri);
        } else {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text('Nelze poslat SMS na číslo $_contactPhone')),
          );
        }
      } catch (e) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Chyba při odesílání SMS: $e')),
        );
      }
    }
  }

  void _sendMessage() {
    if (_messageController.text.trim().isNotEmpty) {
      setState(() {
        _messages.add({
          'sender': 'Já',
          'message': _messageController.text.trim(),
          'time': TimeOfDay.now().format(context),
        });
      });
      _messageController.clear();
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(_contactName ?? 'Chat'),
            if (_rideInfo != null)
              Text(
                _rideInfo!,
                style: const TextStyle(fontSize: 12, fontWeight: FontWeight.normal),
              ),
          ],
        ),
        actions: [
          if (_contactPhone != null)
            IconButton(
              icon: const Icon(Icons.phone),
              onPressed: _makePhoneCall,
              tooltip: 'Zavolat $_contactPhone',
            ),
          IconButton(
            icon: const Icon(Icons.info),
            onPressed: () {
              showDialog(
                context: context,
                builder: (context) => AlertDialog(
                  title: const Text('Kontakt'),
                  content: Column(
                    mainAxisSize: MainAxisSize.min,
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text('Jméno: ${_contactName ?? 'Neznámé'}'),
                      Text('Telefon: ${_contactPhone ?? 'Neznámé'}'),
                      Text('Jízda: ${_rideInfo ?? 'Neznámá'}'),
                    ],
                  ),
                  actions: [
                    TextButton(
                      onPressed: () => Navigator.pop(context),
                      child: const Text('Zavřít'),
                    ),
                  ],
                ),
              );
            },
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
                final isMe = message['sender'] == 'Já';
                return Align(
                  alignment: isMe ? Alignment.centerRight : Alignment.centerLeft,
                  child: Container(
                    margin: const EdgeInsets.all(8),
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: isMe ? Colors.blue.shade100 : Colors.grey.shade200,
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(message['sender']!, style: const TextStyle(fontWeight: FontWeight.bold)),
                        Text(message['message']!),
                        Text(message['time']!, style: const TextStyle(fontSize: 12, color: Colors.grey)),
                      ],
                    ),
                  ),
                );
              },
            ),
          ),
          Container(
            padding: const EdgeInsets.all(8.0),
            decoration: BoxDecoration(
              color: Colors.grey.shade100,
              border: Border(top: BorderSide(color: Colors.grey.shade300)),
            ),
            child: Column(
              children: [
                if (_contactPhone != null)
                  Container(
                    width: double.infinity,
                    padding: const EdgeInsets.symmetric(vertical: 8),
                    child: Row(
                      mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                      children: [
                        ElevatedButton.icon(
                          onPressed: _makePhoneCall,
                          icon: const Icon(Icons.phone),
                          label: Text('Zavolat\n$_contactPhone'),
                          style: ElevatedButton.styleFrom(
                            backgroundColor: Colors.green,
                            foregroundColor: Colors.white,
                          ),
                        ),
                        ElevatedButton.icon(
                          onPressed: _sendSMS,
                          icon: const Icon(Icons.sms),
                          label: Text('SMS\n$_contactPhone'),
                          style: ElevatedButton.styleFrom(
                            backgroundColor: Colors.blue,
                            foregroundColor: Colors.white,
                          ),
                        ),
                      ],
                    ),
                  ),
                Row(
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
                    IconButton(
                      onPressed: _sendMessage,
                      icon: const Icon(Icons.send),
                    ),
                  ],
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}