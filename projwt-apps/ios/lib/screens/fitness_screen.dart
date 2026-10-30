import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/projwt_provider.dart';

class FitnessScreen extends StatefulWidget {
  const FitnessScreen({Key? key}) : super(key: key);

  @override
  State<FitnessScreen> createState() => _FitnessScreenState();
}

class _FitnessScreenState extends State<FitnessScreen> {
  int _selectedDay = 0; // 0 = today

  @override
  void initState() {
    super.initState();
    Future.microtask(
      () => context.read<ProjWTProvider>().initializeFitnessData(),
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
              // Live Heart Rate Card
              _buildLiveHeartRateCard(context, provider),
              const SizedBox(height: 16),

              // Key Metrics Row
              _buildMetricsRow(context, provider),
              const SizedBox(height: 24),

              // 7-Day Graph
              _buildHistoryGraph(context, provider),
              const SizedBox(height: 24),

              // Health Zones
              _buildHealthZones(context),
              const SizedBox(height: 16),

              // Daily Summary
              _buildDailySummary(context, provider),
            ],
          ),
        );
      },
    );
  }

  Widget _buildLiveHeartRateCard(BuildContext context, ProjWTProvider provider) {
    final hr = provider.heartRate;
    final zone = _getHeartRateZone(hr);

    return Card(
      elevation: 4,
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          children: [
            // Pulsing indicator
            Container(
              width: 80,
              height: 80,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                color: zone.color.withOpacity(0.2),
                border: Border.all(color: zone.color, width: 2),
              ),
              child: Center(
                child: Icon(
                  Icons.favorite,
                  size: 40,
                  color: zone.color,
                ),
              ),
            ),
            const SizedBox(height: 16),

            // Heart rate number
            Text(
              '$hr',
              style: Theme.of(context).textTheme.displaySmall?.copyWith(
                color: zone.color,
                fontWeight: FontWeight.bold,
              ),
            ),

            // BPM + Zone
            Text(
              'BPM • ${zone.name}',
              style: Theme.of(context).textTheme.labelLarge?.copyWith(
                color: Colors.grey[600],
              ),
            ),

            // Zone description
            const SizedBox(height: 8),
            Chip(
              label: Text(zone.description),
              backgroundColor: zone.color.withOpacity(0.1),
              labelStyle: TextStyle(color: zone.color),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildMetricsRow(BuildContext context, ProjWTProvider provider) {
    final calories = (provider.heartRate - 60) * 0.05; // Rough estimate

    return Row(
      children: [
        Expanded(
          child: _buildMetricCard(
            context,
            'Calories',
            '${calories.toStringAsFixed(0)} kcal',
            Icons.fire_truck,
            Colors.orange,
          ),
        ),
        const SizedBox(width: 12),
        Expanded(
          child: _buildMetricCard(
            context,
            'Battery',
            '${provider.battery}%',
            Icons.battery_full,
            Colors.green,
          ),
        ),
        const SizedBox(width: 12),
        Expanded(
          child: _buildMetricCard(
            context,
            'Steps',
            '${(provider.heartRate ~/ 2)} steps',
            Icons.directions_walk,
            Colors.blue,
          ),
        ),
      ],
    );
  }

  Widget _buildMetricCard(
    BuildContext context,
    String label,
    String value,
    IconData icon,
    Color color,
  ) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          children: [
            Icon(icon, color: color, size: 24),
            const SizedBox(height: 8),
            Text(
              value,
              style: Theme.of(context).textTheme.titleSmall?.copyWith(
                fontWeight: FontWeight.bold,
              ),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 4),
            Text(
              label,
              style: Theme.of(context).textTheme.labelSmall,
              textAlign: TextAlign.center,
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildHistoryGraph(BuildContext context, ProjWTProvider provider) {
    final historicalData = provider.getHistoricalHeartRate();
    final maxHR = (historicalData.reduce((a, b) => a > b ? a : b) + 20).toDouble();

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              '7-Day Heart Rate',
              style: Theme.of(context).textTheme.titleSmall,
            ),
            const SizedBox(height: 16),

            // Simple bar chart
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceEvenly,
              crossAxisAlignment: CrossAxisAlignment.end,
              children: List.generate(
                historicalData.length,
                (i) {
                  final hr = historicalData[i];
                  final height = (hr / maxHR) * 100;
                  final daysAgo = 6 - i;

                  return Column(
                    children: [
                      Container(
                        width: 30,
                        height: height,
                        decoration: BoxDecoration(
                          color: _getHeartRateZone(hr).color,
                          borderRadius: BorderRadius.circular(4),
                        ),
                      ),
                      const SizedBox(height: 8),
                      Text(
                        daysAgo == 0 ? 'Today' : '${daysAgo}d',
                        style: Theme.of(context).textTheme.labelSmall,
                      ),
                    ],
                  );
                },
              ),
            ),

            const SizedBox(height: 16),

            // Stats line
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceAround,
              children: [
                _buildStatLine('Avg', '${(historicalData.reduce((a, b) => a + b) ~/ historicalData.length)} BPM'),
                _buildStatLine('Max', '${historicalData.reduce((a, b) => a > b ? a : b)} BPM'),
                _buildStatLine('Min', '${historicalData.reduce((a, b) => a < b ? a : b)} BPM'),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildStatLine(String label, String value) {
    return Column(
      children: [
        Text(label, style: const TextStyle(fontSize: 12, color: Colors.grey)),
        const SizedBox(height: 4),
        Text(value, style: const TextStyle(fontSize: 14, fontWeight: FontWeight.bold)),
      ],
    );
  }

  Widget _buildHealthZones(BuildContext context) {
    final zones = [
      (name: 'Resting', range: '< 60 BPM', color: Colors.blue),
      (name: 'Light', range: '60-100 BPM', color: Colors.green),
      (name: 'Moderate', range: '100-140 BPM', color: Colors.orange),
      (name: 'Intense', range: '140+ BPM', color: Colors.red),
    ];

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Heart Rate Zones',
              style: Theme.of(context).textTheme.titleSmall,
            ),
            const SizedBox(height: 12),
            ...zones.map((zone) => Padding(
              padding: const EdgeInsets.symmetric(vertical: 8),
              child: Row(
                children: [
                  Container(
                    width: 12,
                    height: 12,
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      color: zone.color,
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(zone.name, style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w600)),
                        Text(zone.range, style: TextStyle(fontSize: 12, color: Colors.grey[600])),
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

  Widget _buildDailySummary(BuildContext context, ProjWTProvider provider) {
    return Card(
      color: Colors.blue.withOpacity(0.1),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Today\'s Summary',
              style: Theme.of(context).textTheme.titleSmall,
            ),
            const SizedBox(height: 12),
            _buildSummaryRow('Active Minutes', '42 min'),
            _buildSummaryRow('Avg HR', '78 BPM'),
            _buildSummaryRow('Data Points', '${provider.heartRate * 10} samples'),
            _buildSummaryRow('Band Battery', '${provider.battery}%'),
          ],
        ),
      ),
    );
  }

  Widget _buildSummaryRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label, style: const TextStyle(fontSize: 14)),
          Text(value, style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w600)),
        ],
      ),
    );
  }

  HeartRateZone _getHeartRateZone(int hr) {
    if (hr < 60) {
      return HeartRateZone(
        name: 'Resting',
        description: 'Rest & recovery',
        color: Colors.blue,
      );
    } else if (hr < 100) {
      return HeartRateZone(
        name: 'Light',
        description: 'Easy activity',
        color: Colors.green,
      );
    } else if (hr < 140) {
      return HeartRateZone(
        name: 'Moderate',
        description: 'Sustained effort',
        color: Colors.orange,
      );
    } else {
      return HeartRateZone(
        name: 'Intense',
        description: 'Max effort',
        color: Colors.red,
      );
    }
  }
}

class HeartRateZone {
  final String name;
  final String description;
  final Color color;

  HeartRateZone({
    required this.name,
    required this.description,
    required this.color,
  });
}
