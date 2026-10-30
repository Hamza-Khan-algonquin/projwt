import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/projwt_provider.dart';
import 'whoop_connect_screen.dart';

class GesturesScreen extends StatefulWidget {
  const GesturesScreen({Key? key}) : super(key: key);

  @override
  State<GesturesScreen> createState() => _GesturesScreenState();
}

class _GesturesScreenState extends State<GesturesScreen> {
  bool _isScanning = false;

  @override
  void initState() {
    super.initState();
    Future.microtask(
      () => context.read<ProjWTProvider>().initializeGestures(),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Consumer<ProjWTProvider>(
      builder: (context, provider, _) {
        return SingleChildScrollView(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              // WHOOP Band Connection Card
              _buildConnectionCard(context, provider),
              const SizedBox(height: 24),

              // Gesture Vocabulary
              _buildGestureVocabulary(context),
              const SizedBox(height: 24),

              // Test Gestures
              _buildTestGesturesSection(context, provider),
              const SizedBox(height: 24),

              // Gesture History
              _buildGestureHistory(context, provider),
            ],
          ),
        );
      },
    );
  }

  Widget _buildConnectionCard(BuildContext context, ProjWTProvider provider) {
    final isConnected = provider.isBandConnected;
    final bandAddress = provider.bandAddress ?? 'Not connected';
    final signal = provider.bandSignalStrength ?? 0;

    return Card(
      elevation: 4,
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Container(
                  width: 12,
                  height: 12,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    color: isConnected ? Colors.green : Colors.red,
                  ),
                ),
                const SizedBox(width: 12),
                Text(
                  isConnected ? 'WHOOP Band Connected' : 'WHOOP Band Disconnected',
                  style: Theme.of(context).textTheme.titleMedium,
                ),
              ],
            ),
            const SizedBox(height: 16),

            // Band Info
            _buildInfoRow('Address', bandAddress),
            _buildInfoRow('Signal Strength', '${signal}%'),
            _buildInfoRow('Last Sync', provider.lastGestureTime ?? 'Never'),
            const SizedBox(height: 16),

            // Connect & Scan Buttons
            Row(
              children: [
                Expanded(
                  child: ElevatedButton.icon(
                    onPressed: () => Navigator.push(
                      context,
                      MaterialPageRoute(
                        builder: (context) => const WHOOPConnectScreen(),
                      ),
                    ),
                    icon: const Icon(Icons.bluetooth),
                    label: const Text('Connect Band'),
                    style: ElevatedButton.styleFrom(
                      padding: const EdgeInsets.symmetric(vertical: 12),
                      backgroundColor: Colors.green,
                      foregroundColor: Colors.white,
                    ),
                  ),
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: ElevatedButton.icon(
                    onPressed: _isScanning ? null : () => _scanForBand(context, provider),
                    icon: const Icon(Icons.bluetooth_searching),
                    label: Text(_isScanning ? 'Scanning...' : 'Scan'),
                    style: ElevatedButton.styleFrom(
                      padding: const EdgeInsets.symmetric(vertical: 12),
                      backgroundColor: Colors.blue,
                      foregroundColor: Colors.white,
                    ),
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildInfoRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label, style: const TextStyle(fontSize: 14, color: Colors.grey)),
          Text(value, style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w600)),
        ],
      ),
    );
  }

  Widget _buildGestureVocabulary(BuildContext context) {
    final gestures = [
      (
        name: 'Single Tap',
        description: 'Cycle to next command',
        icon: Icons.touch_app,
        color: Colors.blue,
      ),
      (
        name: 'Double Tap',
        description: 'ARM the system',
        icon: Icons.touch_app,
        color: Colors.green,
      ),
      (
        name: 'Dwell (2.5s)',
        description: 'Confirm selected command',
        icon: Icons.timer,
        color: Colors.orange,
      ),
      (
        name: 'Shake',
        description: 'PANIC — immediate disarm',
        icon: Icons.warning,
        color: Colors.red,
      ),
    ];

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Gesture Vocabulary',
              style: Theme.of(context).textTheme.titleSmall,
            ),
            const SizedBox(height: 12),
            ...gestures.map((g) => Padding(
              padding: const EdgeInsets.symmetric(vertical: 8),
              child: Row(
                children: [
                  Container(
                    width: 48,
                    height: 48,
                    decoration: BoxDecoration(
                      color: g.color.withOpacity(0.2),
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: Icon(g.icon, color: g.color, size: 24),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          g.name,
                          style: const TextStyle(
                            fontSize: 14,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                        Text(
                          g.description,
                          style: TextStyle(
                            fontSize: 12,
                            color: Colors.grey[600],
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            )).toList(),
          ],
        ),
      ),
    );
  }

  Widget _buildTestGesturesSection(BuildContext context, ProjWTProvider provider) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Test Gestures',
          style: Theme.of(context).textTheme.titleMedium,
        ),
        const SizedBox(height: 12),
        Row(
          children: [
            Expanded(
              child: ElevatedButton.icon(
                onPressed: provider.isLoading ? null : () => _sendTestGesture(context, provider, 'tap'),
                icon: const Icon(Icons.touch_app),
                label: const Text('Tap'),
                style: ElevatedButton.styleFrom(
                  padding: const EdgeInsets.symmetric(vertical: 12),
                  backgroundColor: Colors.blue,
                ),
              ),
            ),
            const SizedBox(width: 8),
            Expanded(
              child: ElevatedButton.icon(
                onPressed: provider.isLoading ? null : () => _sendTestGesture(context, provider, 'double_tap'),
                icon: const Icon(Icons.touch_app),
                label: const Text('Double Tap'),
                style: ElevatedButton.styleFrom(
                  padding: const EdgeInsets.symmetric(vertical: 12),
                  backgroundColor: Colors.green,
                ),
              ),
            ),
          ],
        ),
        const SizedBox(height: 8),
        Row(
          children: [
            Expanded(
              child: ElevatedButton.icon(
                onPressed: provider.isLoading ? null : () => _sendTestGesture(context, provider, 'dwell'),
                icon: const Icon(Icons.timer),
                label: const Text('Dwell'),
                style: ElevatedButton.styleFrom(
                  padding: const EdgeInsets.symmetric(vertical: 12),
                  backgroundColor: Colors.orange,
                ),
              ),
            ),
            const SizedBox(width: 8),
            Expanded(
              child: ElevatedButton.icon(
                onPressed: provider.isLoading ? null : () => _sendTestGesture(context, provider, 'shake'),
                icon: const Icon(Icons.warning),
                label: const Text('Shake'),
                style: ElevatedButton.styleFrom(
                  padding: const EdgeInsets.symmetric(vertical: 12),
                  backgroundColor: Colors.red,
                  foregroundColor: Colors.white,
                ),
              ),
            ),
          ],
        ),
      ],
    );
  }

  Widget _buildGestureHistory(BuildContext context, ProjWTProvider provider) {
    final history = provider.gestureHistory;

    if (history.isEmpty) {
      return Card(
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Text(
            'No gestures received yet',
            textAlign: TextAlign.center,
            style: Theme.of(context).textTheme.bodySmall,
          ),
        ),
      );
    }

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  'Gesture History',
                  style: Theme.of(context).textTheme.titleSmall,
                ),
                TextButton(
                  onPressed: () => context.read<ProjWTProvider>().clearGestureHistory(),
                  child: const Text('Clear'),
                ),
              ],
            ),
            const SizedBox(height: 12),
            ...history.take(10).map((g) => Padding(
              padding: const EdgeInsets.symmetric(vertical: 6),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Expanded(
                    child: Text(
                      g['gesture'] ?? 'Unknown',
                      style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w600),
                    ),
                  ),
                  Text(
                    g['time'] ?? '',
                    style: TextStyle(fontSize: 12, color: Colors.grey[600]),
                  ),
                ],
              ),
            )).toList(),
          ],
        ),
      ),
    );
  }

  Future<void> _scanForBand(BuildContext context, ProjWTProvider provider) async {
    setState(() => _isScanning = true);

    // Simulate scan
    await Future.delayed(const Duration(seconds: 3));

    setState(() => _isScanning = false);

    if (!mounted) return;

    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Text('WHOOP band found!'),
        backgroundColor: Colors.green,
      ),
    );
  }

  void _sendTestGesture(BuildContext context, ProjWTProvider provider, String gesture) {
    provider.recordGesture(gesture);

    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text('Gesture sent: $gesture'),
        duration: const Duration(seconds: 2),
      ),
    );
  }
}
