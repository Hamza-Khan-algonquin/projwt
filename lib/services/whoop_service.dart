import 'package:flutter_blue_plus/flutter_blue_plus.dart';
import 'package:logger/logger.dart';

class WhoopService {
  static final WhoopService _instance = WhoopService._internal();
  factory WhoopService() => _instance;
  WhoopService._internal();

  final logger = Logger();
  BluetoothDevice? _connectedDevice;

  Stream<BluetoothConnectionState>? _connectionStateStream;

  Future<void> startScan() async {
    try {
      logger.i('Starting BLE scan for WHOOP band...');
      await FlutterBluePlus.startScan(
        timeout: const Duration(seconds: 15),
        withServices: [],
      );
    } catch (e) {
      logger.e('Scan error: $e');
    }
  }

  Future<void> connectToDevice(BluetoothDevice device) async {
    try {
      logger.i('Connecting to ${device.name}...');
      await device.connect();
      _connectedDevice = device;
      logger.i('Connected to ${device.name}');
    } catch (e) {
      logger.e('Connection error: $e');
    }
  }

  Future<void> disconnect() async {
    try {
      if (_connectedDevice != null) {
        await _connectedDevice!.disconnect();
        _connectedDevice = null;
        logger.i('Disconnected from WHOOP band');
      }
    } catch (e) {
      logger.e('Disconnect error: $e');
    }
  }

  Stream<BluetoothConnectionState> get connectionState {
    if (_connectedDevice == null) {
      return Stream.value(BluetoothConnectionState.disconnected);
    }
    return _connectedDevice!.connectionState;
  }

  bool get isConnected => _connectedDevice?.isConnected ?? false;
  String? get deviceName => _connectedDevice?.name;

  // Mock biometric data for now
  Map<String, dynamic> getMockBiometrics() {
    return {
      'heart_rate': (60 + (DateTime.now().millisecond % 40)).toInt(),
      'recovery_score': 72,
      'strain_score': 4.2,
      'sleep_hours': 7.5,
      'skin_temperature': 98.2,
      'timestamp': DateTime.now(),
    };
  }
}
