import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/projwt_provider.dart';

class WHOOPConnectScreen extends StatefulWidget {
  const WHOOPConnectScreen({Key? key}) : super(key: key);

  @override
  State<WHOOPConnectScreen> createState() => _WHOOPConnectScreenState();
}

class _WHOOPConnectScreenState extends State<WHOOPConnectScreen> {
  bool _isScanning = false;
  final List<Map<String, dynamic>> _availableDevices = [
    {
      'name': 'WHOOP 4.0',
      'address': 'F0:A3:47:92:11:84',
      'rssi': -45,
      'connected': false,
    },
    {
      'name': 'WHOOP Band Gen4',
      'address': 'E8:2A:15:C4:09:21',
      'rssi': -67,
      'connected': false,
    },
    {
      'name': 'WHOOP Device',
      'address': 'D4:5C:8F:77:33:12',
      'rssi': -78,
      'connected': false,
    },
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Connect WHOOP Band'),
        leading: IconButton(
          icon: const Icon(Icons.close),
          onPressed: () => Navigator.pop(context),
        ),
      ),
      body: Consumer<ProjWTProvider>(
        builder: (context, provider, _) {
          return SingleChildScrollView(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                // Info Card
                _buildInfoCard(context),
                const SizedBox(height: 24),

                // Scan Button
                ElevatedButton.icon(
                  onPressed: _isScanning ? null : _startScan,
                  icon: const Icon(Icons.bluetooth_searching),
                  label: Text(_isScanning ? 'Scanning...' : 'Scan for WHOOP Bands'),
                  style: ElevatedButton.styleFrom(
                    padding: const EdgeInsets.symmetric(vertical: 12),
                    backgroundColor: Colors.blue,
                    foregroundColor: Colors.white,
                  ),
                ),
                const SizedBox(height: 24),

                // Available Devices
                Text(
                  'Available Devices',
                  style: Theme.of(context).textTheme.titleMedium,
                ),
                const SizedBox(height: 12),
                ..._availableDevices.map((device) {
                  final signalStrength = _getSignalStrength(device['rssi']);
                  return _buildDeviceCard(context, device, signalStrength, provider);
                }).toList(),

                const SizedBox(height: 24),

                // Permissions Info
                _buildPermissionsCard(context),
              ],
            ),
          );
        },
      ),
    );
  }

  Widget _buildInfoCard(BuildContext context) {
    return Card(
      color: Colors.blue.withOpacity(0.1),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'How to Connect',
              style: Theme.of(context).textTheme.titleSmall,
            ),
            const SizedBox(height: 12),
            _buildStep(
              context,
              '1',
              'Make sure your WHOOP band is powered on and in range',
            ),
            _buildStep(
              context,
              '2',
              'Tap "Scan for WHOOP Bands" below',
            ),
            _buildStep(
              context,
              '3',
              'Select your band from the list',
            ),
            _buildStep(
              context,
              '4',
              'Grant Bluetooth permission when prompted',
            ),
            _buildStep(
              context,
              '5',
              'Band will connect automatically',
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildStep(BuildContext context, String number, String text) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6),
      child: Row(
        children: [
          Container(
            width: 24,
            height: 24,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              color: Colors.blue,
            ),
            child: Center(
              child: Text(
                number,
                style: const TextStyle(
                  color: Colors.white,
                  fontWeight: FontWeight.bold,
                  fontSize: 12,
                ),
              ),
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Text(
              text,
              style: Theme.of(context).textTheme.bodySmall,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildDeviceCard(
    BuildContext context,
    Map<String, dynamic> device,
    String signalStrength,
    ProjWTProvider provider,
  ) {
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        device['name'],
                        style: Theme.of(context).textTheme.titleSmall,
                      ),
                      const SizedBox(height: 4),
                      Text(
                        device['address'],
                        style: Theme.of(context).textTheme.labelSmall,
                      ),
                    ],
                  ),
                ),
                Column(
                  alignItems: CrossAxisAlignment.end,
                  children: [
                    _buildSignalBars(device['rssi']),
                    const SizedBox(height: 4),
                    Text(
                      signalStrength,
                      style: TextStyle(
                        fontSize: 12,
                        color: Colors.grey[600],
                      ),
                    ),
                  ],
                ),
              ],
            ),
            const SizedBox(height: 12),
            SizedBox(
              width: double.infinity,
              child: ElevatedButton.icon(
                onPressed: () => _connectDevice(context, device, provider),
                icon: const Icon(Icons.bluetooth_connected),
                label: const Text('Connect'),
                style: ElevatedButton.styleFrom(
                  padding: const EdgeInsets.symmetric(vertical: 10),
                  backgroundColor: Colors.green,
                  foregroundColor: Colors.white,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildSignalBars(int rssi) {
    return Row(
      children: [
        for (int i = 0; i < 4; i++)
          Padding(
            padding: const EdgeInsets.only(right: 2),
            child: Container(
              width: 2,
              height: 8 + (i * 3).toDouble(),
              decoration: BoxDecoration(
                color: _getSignalColor(rssi, i),
                borderRadius: BorderRadius.circular(1),
              ),
            ),
          ),
      ],
    );
  }

  Color _getSignalColor(int rssi, int barIndex) {
    final strength = _getSignalQuality(rssi);
    if (strength >= barIndex) {
      return rssi > -50
          ? Colors.green
          : rssi > -70
              ? Colors.orange
              : Colors.red;
    }
    return Colors.grey[300]!;
  }

  int _getSignalQuality(int rssi) {
    if (rssi > -50) return 4;
    if (rssi > -60) return 3;
    if (rssi > -70) return 2;
    return 1;
  }

  String _getSignalStrength(int rssi) {
    if (rssi > -50) return 'Excellent';
    if (rssi > -60) return 'Good';
    if (rssi > -70) return 'Fair';
    return 'Weak';
  }

  Widget _buildPermissionsCard(BuildContext context) {
    return Card(
      color: Colors.amber.withOpacity(0.1),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Bluetooth Permissions',
              style: Theme.of(context).textTheme.titleSmall,
            ),
            const SizedBox(height: 12),
            Text(
              'ProjWT needs permission to:',
              style: Theme.of(context).textTheme.bodySmall,
            ),
            const SizedBox(height: 8),
            _buildPermissionRow('Scan for Bluetooth devices'),
            _buildPermissionRow('Connect to nearby devices'),
            _buildPermissionRow('Read biometric data'),
          ],
        ),
      ),
    );
  }

  Widget _buildPermissionRow(String permission) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        children: [
          const Icon(Icons.check_circle, size: 16, color: Colors.green),
          const SizedBox(width: 8),
          Expanded(
            child: Text(
              permission,
              style: const TextStyle(fontSize: 13),
            ),
          ),
        ],
      ),
    );
  }

  Future<void> _startScan() async {
    setState(() => _isScanning = true);

    // Simulate scan
    await Future.delayed(const Duration(seconds: 2));

    setState(() => _isScanning = false);

    if (!mounted) return;

    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: const Text('Found ${_availableDevices.length} WHOOP devices'),
        backgroundColor: Colors.green,
      ),
    );
  }

  void _connectDevice(
    BuildContext context,
    Map<String, dynamic> device,
    ProjWTProvider provider,
  ) {
    // Simulate connection
    provider.connectWHOOPBand(
      name: device['name'],
      address: device['address'],
      signalStrength: _getSignalQuality(device['rssi']) * 25,
    );

    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text('Connected to ${device['name']}'),
        backgroundColor: Colors.green,
      ),
    );

    Future.delayed(const Duration(milliseconds: 500), () {
      if (mounted) Navigator.pop(context);
    });
  }
}
