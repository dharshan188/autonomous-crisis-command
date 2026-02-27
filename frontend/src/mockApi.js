export const mockCrisisCommand = (crisisText, approved) => {
  return new Promise((resolve) => {
    setTimeout(() => {
      const riskScore =
        crisisText.toLowerCase().includes("explosion")
          ? 5
          : crisisText.toLowerCase().includes("fire")
          ? 4
          : 2;

      if (!approved && riskScore >= 4) {
        resolve({
          status: "PENDING_APPROVAL",
          details: [
            {
              crisis_type: "Fire",
              location: "Sector 3",
              risk_score: riskScore,
            },
          ],
        });
      } else {
        resolve({
          status: "EXECUTED",
          execution_result: {
            execution_status: "DISPATCHED",
            dispatch_units: ["Fire Truck A1", "Ambulance B2"],
            eta: "5 mins",
            decisions: [
              {
                risk_score: riskScore,
              },
            ],
          },
          alerts: [
            "Nearby hospital notified",
            "Utilities department alerted",
          ],
        });
      }
    }, 1200);
  });
};

export const mockAuditLogs = () => {
  return [
    {
      timestamp: "2026-02-27 10:15",
      event: "CRISIS_RECEIVED",
      details: "Fire reported in Sector 3",
    },
    {
      timestamp: "2026-02-27 10:16",
      event: "DECISION_MADE",
      details: "Allocated Fire Unit A1",
    },
    {
      timestamp: "2026-02-27 10:17",
      event: "EXECUTION_COMPLETED",
      details: "Dispatch confirmed",
    },
  ];
};