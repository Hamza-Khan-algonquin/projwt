import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/projwt_provider.dart';

class BiometricsScreen extends StatefulWidget {
  const BiometricsScreen({Key? key}) : super(key: key);

  @override
  State<BiometricsScreen> createState() => _BiometricsScreenState();
}

class _BiometricsScreenState extends State<BiometricsScreen> {
  late Stream<Map<String, dynamic>> _bioStream;

  @override
  void initState() {
    super.initState();
    _bioStream = context.read<ProjWTProvider>().getBiometricsStream();
  }

  @override
  Widget build(BuildContext context) {
    return StreamBuilder<Map<String, dynamic>>(
      stream: _bioStream,
      builder: (context, snapshot) {
        return SingleChildScrollView(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              // Heart Rate Card
              _buildHeartRateCard(context),
              const SizedBox(height: 16),

              // Battery Card
              _buildBatteryCard(context),
              const SizedBox(height: 24),

              // Stats Section
              _buildStatsSection(context, snapshot),
              const SizedBox(height: 16),

              // Connection Status
              _buildConnectionStatus(context, snapshot),
            ],
          ),
        );
      },
    );
  }

  Widget _buildHeartRateCard(BuildContext context) {
    return Consumer<ProjWTProvider>(
      builder: (context, provider, _) {
        final hr = provider.heartRate;
        final status = _getHeartRateStatus(hr);

        return Card(
          elevation: 4,
          child: Padding(
            padding: const EdgeInsets.all(24),
            child: Column(
              children: [
                Icon(
                  Icons.favorite,
                  size: 48,
                  color: status.color,
                ),
                const SizedBox(height: 16),
                Text(
                  '$hr',
                  style: Theme.of(context).textTheme.displaySmall?.copyWith(
                    color: status.color,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                const SizedBox(height: 8),
                Text(
                  'BPM',
                  style: Theme.of(context).textTheme.labelLarge,
                ),
                const SizedBox(height: 8),
                Text(
                  status.label,
                  style: Theme.of(context).textTheme.bodySmall?.copyWith(
                    color: status.color,
                  ),
                ),
              ],
            ),
          ),
        );
      },
    );
  }

  Widget _buildBatteryCard(BuildContext context) {
    return Consumer<ProjWTProvider>(
      builder: (context, provider, _) {
        final battery = provider.battery;
        final statusColor = battery > 50
            ? Colors.green
            : battery > 20
                ? Colors.orange
                : Colors.red;

        return Card(
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'WHOOP Band Battery',
                  style: Theme.of(context).textTheme.titleSmall,
                ),
                const SizedBox(height: 12),
                Row(
                  children: [
                    Expanded(
                      child: ClipRRect(
                        borderRadius: BorderRadius.circular(8),
                        child: LinearProgressIndicator(
                          value: battery / 100,
                          minHeight: 8,
                          backgroundColor: Colors.grey[300],
                          valueColor:
                              AlwaysStoppedAnimation<Color>(statusColor),
                        ),
                      ),
                    ),
                    const SizedBox(width: 12),
                    Text(
                      '$battery%',
                      style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                        color: statusColor,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
        );
      },
    );
  }

  Widget _buildStatsSection(
    BuildContext context,
    AsyncSnapshot<Map<String, dynamic>> snapshot,
  ) {
    if (!snapshot.hasData || snapshot.data!.containsKey('error')) {
      return Card(
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Text(
            'Waiting for biometric data...',
            textAlign: TextAlign.center,
            style: Theme.of(context).textTheme.bodySmall,
          ),
        ),
      );
    }

    final data = snapshot.data!;
    final timestamp =
        data['timestamp'] ?? DateTime.now().toIso8601String();
    final lastUpdate = DateTime.parse(timestamp);
    final timeAgo = DateTime.now().difference(lastUpdate);

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Stream Information',
              style: Theme.of(context).textTheme.titleSmall,
            ),
            const SizedBox(height: 12),
            _buildStatRow(
              'Last Update',
              timeAgo.inSeconds < 60
                  ? '${timeAgo.inSeconds}s ago'
                  : '${timeAgo.inMinutes}m ago',
            ),
            const SizedBox(height: 8),
            _buildStatRow(
              'Data Frequency',
              '~1 Hz',
            ),
            const SizedBox(height: 8),
            _buildStatRow(
              'Protocol',
              'WebSocket',
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildConnectionStatus(
    BuildContext context,
    AsyncSnapshot<Map<String, dynamic>> snapshot,
  ) {
    final isConnected = snapshot.hasData && !snapshot.data!.containsKey('error');

    return Card(
      color: isConnected ? Colors.green.withOpacity(0.1) : Colors.red.withOpacity(0.1),
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Row(
          children: [
            Icon(
              isConnected ? Icons.cloud_done : Icons.cloud_off,
              color: isConnected ? Colors.green : Colors.red,
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Text(
                isConnected
                    ? 'Connected to biometric stream'
                    : 'Waiting for connection...',
                style: TextStyle(
                  color: isConnected ? Colors.green : Colors.red,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildStatRow(String label, String value) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Text(
          label,
          style: const TextStyle(fontSize: 14),
        ),
        Text(
          value,
          style: const TextStyle(
            fontSize: 14,
            fontWeight: FontWeight.w600,
          ),
        ),
      ],
    );
  }

  HeartRateStatus _getHeartRateStatus(int hr) {
    if (hr == 0) {
      return HeartRateStatus(
        label: 'No data',
        color: Colors.grey,
      );
    } else if (hr < 60) {
      return HeartRateStatus(
        label: 'Low',
        color: Colors.blue,
      );
    } else if (hr < 100) {
      return HeartRateStatus(
        label: 'Normal',
        color: Colors.green,
      );
    } else if (hr < 130) {
      return HeartRateStatus(
        label: 'Elevated',
        color: Colors.orange,
      );
    } else {
      return HeartRateStatus(
        label: 'High',
        color: Colors.red,
      );
    }
  }
}

class HeartRateStatus {
  final String label;
  final Color color;

  HeartRateStatus({
    required this.label,
    required this.color,
  });
}
