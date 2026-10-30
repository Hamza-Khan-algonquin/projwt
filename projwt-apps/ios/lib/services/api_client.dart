import 'package:http/http.dart' as http;
import 'package:web_socket_channel/web_socket_channel.dart';
import 'dart:convert';

class ProjWTAPIClient {
  final String baseUrl;
  late WebSocketChannel _wsChannel;

  ProjWTAPIClient({this.baseUrl = 'http://localhost:8000'});

  // ------- HTTP Methods -------

  Future<Map<String, dynamic>> getHealth() async {
    try {
      final response = await http.get(
        Uri.parse('$baseUrl/health'),
      ).timeout(const Duration(seconds: 5));

      if (response.statusCode == 200) {
        return json.decode(response.body);
      }
      return {'error': 'Failed to get health'};
    } catch (e) {
      return {'error': e.toString()};
    }
  }

  Future<Map<String, dynamic>> getState() async {
    try {
      final response = await http.get(
        Uri.parse('$baseUrl/state'),
      ).timeout(const Duration(seconds: 5));

      if (response.statusCode == 200) {
        return json.decode(response.body);
      }
      return {'error': 'Failed to get state'};
    } catch (e) {
      return {'error': e.toString()};
    }
  }

  Future<List<String>> getCommands() async {
    try {
      final response = await http.get(
        Uri.parse('$baseUrl/commands'),
      ).timeout(const Duration(seconds: 5));

      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        return List<String>.from(data['menu'] ?? []);
      }
      return [];
    } catch (e) {
      return [];
    }
  }

  Future<Map<String, dynamic>> sendCommand(String command) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/command'),
        headers: {'Content-Type': 'application/json'},
        body: json.encode({'command': command}),
      ).timeout(const Duration(seconds: 10));

      if (response.statusCode == 200) {
        return json.decode(response.body);
      }
      return {'ok': false, 'error': 'HTTP ${response.statusCode}'};
    } catch (e) {
      return {'ok': false, 'error': e.toString()};
    }
  }

  Future<Map<String, dynamic>> armGesture() async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/gesture/arm'),
      ).timeout(const Duration(seconds: 5));

      if (response.statusCode == 200) {
        return json.decode(response.body);
      }
      return {'error': 'Failed to arm'};
    } catch (e) {
      return {'error': e.toString()};
    }
  }

  Future<Map<String, dynamic>> panicGesture() async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/gesture/panic'),
      ).timeout(const Duration(seconds: 5));

      if (response.statusCode == 200) {
        return json.decode(response.body);
      }
      return {'error': 'Failed to panic'};
    } catch (e) {
      return {'error': e.toString()};
    }
  }

  // ------- WebSocket Methods -------

  Stream<Map<String, dynamic>> streamBiometrics() {
    final wsUrl = baseUrl.replaceFirst('http://', 'ws://').replaceFirst('https://', 'wss://');
    _wsChannel = WebSocketChannel.connect(
      Uri.parse('$wsUrl/ws/biometrics'),
    );

    return _wsChannel.stream.map((message) {
      try {
        return json.decode(message) as Map<String, dynamic>;
      } catch (e) {
        return {'error': 'Failed to parse message'};
      }
    });
  }

  void closeBiometricStream() {
    _wsChannel.sink.close();
  }
}
