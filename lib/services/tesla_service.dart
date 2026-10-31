import 'package:dio/dio.dart';
import 'package:logger/logger.dart';

class TeslaService {
  static final TeslaService _instance = TeslaService._internal();
  factory TeslaService() => _instance;
  TeslaService._internal();

  final logger = Logger();
  late Dio _dio;
  String? _accessToken;
  String? _vehicleId;

  void initialize(String accessToken, String vehicleId) {
    _accessToken = accessToken;
    _vehicleId = vehicleId;

    _dio = Dio(BaseOptions(
      baseUrl: 'https://api.tesla.com/api/1',
      headers: {
        'Authorization': 'Bearer $_accessToken',
        'Content-Type': 'application/json',
      },
    ));

    logger.i('Tesla service initialized with vehicle ID: $_vehicleId');
  }

  bool get isConfigured => _accessToken != null && _vehicleId != null;

  Future<bool> unlock() async {
    if (!isConfigured) {
      logger.w('Tesla not configured');
      return false;
    }
    try {
      logger.i('Sending unlock command...');
      await _dio.post('/vehicles/$_vehicleId/command/door_unlock');
      logger.i('✓ Car unlocked');
      return true;
    } catch (e) {
      logger.e('Unlock error: $e');
      return false;
    }
  }

  Future<bool> lock() async {
    if (!isConfigured) return false;
    try {
      logger.i('Sending lock command...');
      await _dio.post('/vehicles/$_vehicleId/command/door_lock');
      logger.i('✓ Car locked');
      return true;
    } catch (e) {
      logger.e('Lock error: $e');
      return false;
    }
  }

  Future<bool> honk() async {
    if (!isConfigured) return false;
    try {
      logger.i('Sending honk command...');
      await _dio.post('/vehicles/$_vehicleId/command/honk_horn');
      logger.i('✓ Honk sent');
      return true;
    } catch (e) {
      logger.e('Honk error: $e');
      return false;
    }
  }

  Future<bool> flashLights() async {
    if (!isConfigured) return false;
    try {
      logger.i('Sending flash command...');
      await _dio.post('/vehicles/$_vehicleId/command/flash_lights');
      logger.i('✓ Lights flashed');
      return true;
    } catch (e) {
      logger.e('Flash error: $e');
      return false;
    }
  }

  Future<bool> setClimate(double temperature) async {
    if (!isConfigured) return false;
    try {
      logger.i('Setting climate to $temperature°C...');
      await _dio.post(
        '/vehicles/$_vehicleId/command/set_temps',
        data: {'driver_temp': temperature, 'passenger_temp': temperature},
      );
      logger.i('✓ Climate set');
      return true;
    } catch (e) {
      logger.e('Climate error: $e');
      return false;
    }
  }

  Future<bool> startCharging() async {
    if (!isConfigured) return false;
    try {
      logger.i('Starting charge...');
      await _dio.post('/vehicles/$_vehicleId/command/charge_start');
      logger.i('✓ Charging started');
      return true;
    } catch (e) {
      logger.e('Charge error: $e');
      return false;
    }
  }
}
