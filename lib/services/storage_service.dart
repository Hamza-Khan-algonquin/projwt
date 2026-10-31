import 'package:shared_preferences/shared_preferences.dart';
import 'dart:convert';

class StorageService {
  static final StorageService _instance = StorageService._internal();
  factory StorageService() => _instance;
  StorageService._internal();

  late SharedPreferences _prefs;

  Future<void> initialize() async {
    _prefs = await SharedPreferences.getInstance();
  }

  // Tesla credentials
  Future<void> saveTeslaCredentials(String token, String vin) async {
    await _prefs.setString('tesla_token', token);
    await _prefs.setString('tesla_vin', vin);
  }

  String? getTeslaToken() => _prefs.getString('tesla_token');
  String? getTeslaVin() => _prefs.getString('tesla_vin');

  // WHOOP data
  Future<void> saveBiometric(Map<String, dynamic> data) async {
    final List<String> history = _prefs.getStringList('biometric_history') ?? [];
    history.add(jsonEncode(data));

    // Keep only last 100 entries
    if (history.length > 100) {
      history.removeAt(0);
    }

    await _prefs.setStringList('biometric_history', history);
  }

  List<Map<String, dynamic>> getBiometricHistory() {
    final List<String>? history = _prefs.getStringList('biometric_history');
    if (history == null) return [];

    return history
        .map((e) => jsonDecode(e) as Map<String, dynamic>)
        .toList();
  }

  Map<String, dynamic>? getLatestBiometric() {
    final history = getBiometricHistory();
    return history.isEmpty ? null : history.last;
  }

  Future<void> clearBiometricHistory() async {
    await _prefs.remove('biometric_history');
  }
}
