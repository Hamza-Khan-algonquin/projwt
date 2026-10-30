import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/projwt_provider.dart';

class AdvancedFitnessScreen extends StatefulWidget {
  const AdvancedFitnessScreen({Key? key}) : super(key: key);

  @override
  State<AdvancedFitnessScreen> createState() => _AdvancedFitnessScreenState();
}

class _AdvancedFitnessScreenState extends State<AdvancedFitnessScreen> {
  int _selectedTab = 0;

  @override
  void initState() {
    super.initState();
    Future.microtask(
      () => context.read<ProjWTProvider>().initializeAdvancedFitness(),
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
              // Today's Summary Cards
              _buildTodaySummary(context, provider),
              const SizedBox(height: 24),

              // Key Metrics Tabs
              _buildMetricTabs(context),
              const SizedBox(height: 16),

              // Tab Content
              _buildTabContent(context, provider),
            ],
          ),
        );
      },
    );
  }

  Widget _buildTodaySummary(BuildContext context, ProjWTProvider provider) {
    final recovery = provider.recoveryScore;
    final strain = provider.strainScore;
    final sleep = provider.sleepScore;
    final stress = provider.stressLevel;

    return Column(
      children: [
        // Primary Metric (Recovery)
        _buildPrimaryMetric(
          context,
          'Recovery',
          '$recovery%',
          Colors.green,
          'You\'re well recovered and ready for activity',
        ),
        const SizedBox(height: 12),

        // Secondary Metrics Row
        Row(
          children: [
            Expanded(
              child: _buildSecondaryMetric(
                context,
                'Strain',
                strain.toStringAsFixed(1),
                Colors.orange,
                'Today\'s exertion level',
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: _buildSecondaryMetric(
                context,
                'Sleep',
                '$sleep%',
                Colors.blue,
                'Sleep quality score',
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: _buildSecondaryMetric(
                context,
                'Stress',
                stress,
                Colors.red,
                'Stress level',
              ),
            ),
          ],
        ),
      ],
    );
  }

  Widget _buildPrimaryMetric(
    BuildContext context,
    String label,
    String value,
    Color color,
    String subtitle,
  ) {
    return Card(
      elevation: 4,
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          children: [
            Text(label, style: Theme.of(context).textTheme.labelLarge),
            const SizedBox(height: 8),
            Row(
              mainAxisAlignment: MainAxisAlignment.center,
              crossAxisAlignment: CrossAxisAlignment.baseline,
              textBaseline: TextBaseline.alphabetic,
              children: [
                Text(
                  value,
                  style: TextStyle(
                    fontSize: 48,
                    fontWeight: FontWeight.bold,
                    color: color,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 8),
            Text(
              subtitle,
              textAlign: TextAlign.center,
              style: Theme.of(context).textTheme.bodySmall,
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildSecondaryMetric(
    BuildContext context,
    String label,
    String value,
    Color color,
    String subtitle,
  ) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          children: [
            Text(
              label,
              style: Theme.of(context).textTheme.labelSmall,
            ),
            const SizedBox(height: 8),
            Text(
              value,
              style: TextStyle(
                fontSize: 20,
                fontWeight: FontWeight.bold,
                color: color,
              ),
            ),
            const SizedBox(height: 4),
            Text(
              subtitle,
              textAlign: TextAlign.center,
              style: Theme.of(context).textTheme.labelSmall,
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildMetricTabs(BuildContext context) {
    final tabs = ['Overview', 'HRV', 'Sleep', 'Strain'];

    return SingleChildScrollView(
      scrollDirection: Axis.horizontal,
      child: Row(
        children: List.generate(tabs.length, (index) {
          final isSelected = _selectedTab == index;
          return Padding(
            padding: const EdgeInsets.only(right: 8),
            child: FilterChip(
              selected: isSelected,
              onSelected: (selected) {
                setState(() => _selectedTab = index);
              },
              label: Text(tabs[index]),
              backgroundColor: Colors.grey[200],
              selectedColor: Colors.blue,
              labelStyle: TextStyle(
                color: isSelected ? Colors.white : Colors.black,
                fontWeight: isSelected ? FontWeight.w600 : FontWeight.normal,
              ),
            ),
          );
        }),
      ),
    );
  }

  Widget _buildTabContent(BuildContext context, ProjWTProvider provider) {
    switch (_selectedTab) {
      case 0:
        return _buildOverviewTab(context, provider);
      case 1:
        return _buildHRVTab(context, provider);
      case 2:
        return _buildSleepTab(context, provider);
      case 3:
        return _buildStrainTab(context, provider);
      default:
        return const SizedBox();
    }
  }

  Widget _buildOverviewTab(BuildContext context, ProjWTProvider provider) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        _buildMetricCard(
          context,
          'Resting Heart Rate',
          '${provider.restingHeartRate} BPM',
          Colors.blue,
          'Lower is better for recovery',
        ),
        const SizedBox(height: 12),
        _buildMetricCard(
          context,
          'HRV (Heart Rate Variability)',
          '${provider.hrv} ms',
          Colors.green,
          'Higher HRV indicates better recovery',
        ),
        const SizedBox(height: 12),
        _buildMetricCard(
          context,
          'Max Heart Rate',
          '${provider.maxHeartRate} BPM',
          Colors.orange,
          'Peak intensity today',
        ),
        const SizedBox(height: 16),
        _buildWHOOPExplanation(context),
      ],
    );
  }

  Widget _buildHRVTab(BuildContext context, ProjWTProvider provider) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Heart Rate Variability',
          style: Theme.of(context).textTheme.titleMedium,
        ),
        const SizedBox(height: 12),
        Card(
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              children: [
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                  children: [
                    _buildHRVMetric('Last Night', '${provider.hrv} ms', Colors.green),
                    _buildHRVMetric('7-Day Avg', '${(provider.hrv * 0.95).toInt()} ms', Colors.blue),
                    _buildHRVMetric('Trend', '↑ Good', Colors.green),
                  ],
                ),
              ],
            ),
          ),
        ),
        const SizedBox(height: 16),
        Card(
          color: Colors.green.withOpacity(0.1),
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'What is HRV?',
                  style: Theme.of(context).textTheme.titleSmall,
                ),
                const SizedBox(height: 8),
                Text(
                  'Heart Rate Variability measures the variation in time between heartbeats. Higher HRV indicates better recovery and readiness for activity. During sleep, HRV naturally increases.\n\nTrack this metric to optimize training and recovery.',
                  style: Theme.of(context).textTheme.bodySmall,
                ),
              ],
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildHRVMetric(String label, String value, Color color) {
    return Column(
      children: [
        Text(label, style: const TextStyle(fontSize: 12, color: Colors.grey)),
        const SizedBox(height: 4),
        Text(
          value,
          style: TextStyle(
            fontSize: 14,
            fontWeight: FontWeight.bold,
            color: color,
          ),
        ),
      ],
    );
  }

  Widget _buildSleepTab(BuildContext context, ProjWTProvider provider) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Sleep Metrics',
          style: Theme.of(context).textTheme.titleMedium,
        ),
        const SizedBox(height: 12),
        _buildMetricCard(
          context,
          'Duration',
          '${provider.sleepDuration}h ${provider.sleepMinutes}m',
          Colors.blue,
          'Last night\'s total sleep',
        ),
        const SizedBox(height: 12),
        _buildMetricCard(
          context,
          'Quality',
          '${provider.sleepScore}%',
          Colors.green,
          'Sleep quality score',
        ),
        const SizedBox(height: 12),
        Card(
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Sleep Breakdown',
                  style: Theme.of(context).textTheme.titleSmall,
                ),
                const SizedBox(height: 12),
                _buildSleepBreakdown('REM', 1.5, Colors.purple),
                _buildSleepBreakdown('Light', 2.0, Colors.blue),
                _buildSleepBreakdown('Deep', 1.2, Colors.indigo),
                _buildSleepBreakdown('Awake', 0.3, Colors.grey),
              ],
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildSleepBreakdown(String stage, double hours, Color color) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(stage, style: const TextStyle(fontSize: 13)),
              Text('${hours}h', style: const TextStyle(fontWeight: FontWeight.w600)),
            ],
          ),
          const SizedBox(height: 4),
          ClipRRect(
            borderRadius: BorderRadius.circular(4),
            child: LinearProgressIndicator(
              value: hours / 3.0,
              minHeight: 6,
              backgroundColor: Colors.grey[300],
              valueColor: AlwaysStoppedAnimation<Color>(color),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildStrainTab(BuildContext context, ProjWTProvider provider) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Strain Score',
          style: Theme.of(context).textTheme.titleMedium,
        ),
        const SizedBox(height: 12),
        Card(
          elevation: 4,
          child: Padding(
            padding: const EdgeInsets.all(20),
            child: Column(
              children: [
                Text(
                  'Today\'s Strain',
                  style: Theme.of(context).textTheme.labelLarge,
                ),
                const SizedBox(height: 16),
                Stack(
                  alignment: Alignment.center,
                  children: [
                    SizedBox(
                      width: 120,
                      height: 120,
                      child: CircularProgressIndicator(
                        value: provider.strainScore / 21.0,
                        strokeWidth: 8,
                        valueColor: AlwaysStoppedAnimation<Color>(
                          provider.strainScore > 15
                              ? Colors.red
                              : provider.strainScore > 10
                                  ? Colors.orange
                                  : Colors.green,
                        ),
                      ),
                    ),
                    Column(
                      children: [
                        Text(
                          provider.strainScore.toStringAsFixed(1),
                          style: const TextStyle(
                            fontSize: 32,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        const Text(
                          '/ 21',
                          style: TextStyle(fontSize: 12, color: Colors.grey),
                        ),
                      ],
                    ),
                  ],
                ),
                const SizedBox(height: 12),
                Text(
                  _getStrainInterpretation(provider.strainScore),
                  textAlign: TextAlign.center,
                  style: Theme.of(context).textTheme.bodySmall,
                ),
              ],
            ),
          ),
        ),
        const SizedBox(height: 16),
        Card(
          color: Colors.orange.withOpacity(0.1),
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Strain Zones',
                  style: Theme.of(context).textTheme.titleSmall,
                ),
                const SizedBox(height: 8),
                _buildStrainZone('Low (0-7)', 'Rest & recovery', Colors.green),
                _buildStrainZone('Moderate (8-13)', 'Maintenance', Colors.orange),
                _buildStrainZone('High (14-21)', 'Peak performance', Colors.red),
              ],
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildStrainZone(String zone, String description, Color color) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6),
      child: Row(
        children: [
          Container(
            width: 12,
            height: 12,
            decoration: BoxDecoration(shape: BoxShape.circle, color: color),
          ),
          const SizedBox(width: 12),
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(zone, style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 13)),
              Text(description, style: TextStyle(fontSize: 12, color: Colors.grey[600])),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildMetricCard(
    BuildContext context,
    String title,
    String value,
    Color color,
    String subtitle,
  ) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Row(
          children: [
            Container(
              width: 60,
              height: 60,
              decoration: BoxDecoration(
                color: color.withOpacity(0.2),
                borderRadius: BorderRadius.circular(12),
              ),
              child: Center(
                child: Text(
                  value.split(' ')[0],
                  style: TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.bold,
                    color: color,
                  ),
                ),
              ),
            ),
            const SizedBox(width: 16),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(title, style: Theme.of(context).textTheme.titleSmall),
                  const SizedBox(height: 4),
                  Text(subtitle, style: Theme.of(context).textTheme.labelSmall),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildWHOOPExplanation(BuildContext context) {
    return Card(
      color: Colors.blue.withOpacity(0.1),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Recovery = The Master Metric',
              style: Theme.of(context).textTheme.titleSmall,
            ),
            const SizedBox(height: 8),
            Text(
              'Recovery is calculated from 3 inputs:\n\n'
              '• Resting Heart Rate (RHR)\n'
              '• Heart Rate Variability (HRV)\n'
              '• Sleep Quality & Duration\n\n'
              'Green (80%+): Fully recovered, ready for intense activity\n'
              'Yellow (50-79%): Partially recovered, moderate activity OK\n'
              'Red (<50%): Not recovered, light activity recommended',
              style: Theme.of(context).textTheme.bodySmall,
            ),
          ],
        ),
      ),
    );
  }

  String _getStrainInterpretation(double strain) {
    if (strain > 15) {
      return 'High strain. Focus on recovery tonight.';
    } else if (strain > 10) {
      return 'Moderate strain. Balanced day.';
    } else {
      return 'Low strain. Good day for rest.';
    }
  }
}
