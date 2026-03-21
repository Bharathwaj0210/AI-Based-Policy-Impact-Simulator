import jsPDF from 'jspdf';
import autoTable from 'jspdf-autotable';

/**
 * Generates a professional PDF report for Policy Simulations
 */
export const generatePolicyReport = (domain, metrics, filters, geminiData) => {
    const doc = new jsPDF();
    const pageWidth = doc.internal.pageSize.getWidth();
    const dateStr = new Date().toLocaleDateString();

    // 1. Header
    doc.setFontSize(22);
    doc.setTextColor(40, 44, 52);
    doc.text(`Policy Simulation Report`, 14, 22);
    
    doc.setFontSize(14);
    doc.setTextColor(100);
    doc.text(`Domain: ${domain.toUpperCase()}`, 14, 32);
    doc.text(`Date: ${dateStr}`, pageWidth - 50, 32);
    doc.setLineWidth(0.5);
    doc.line(14, 35, pageWidth - 14, 35);

    let yPos = 45;

    // 2. Metrics Section
    doc.setFontSize(16);
    doc.setTextColor(0);
    doc.text('Performance Metrics', 14, yPos);
    yPos += 8;

    const metricsTable = [
        ['Metric', 'Value'],
        ['Total Evaluated', metrics.records_evaluated || metrics.total_records || 0],
        ['Eligible Population', metrics.eligible || metrics.best_case || 0],
        ['Rejected Population', metrics.rejected || metrics.worst_case || 0],
        ['Eligibility Rate', `${((metrics.eligibility_rate || 0) * 100).toFixed(1)}%`]
    ];

    autoTable(doc, {
        startY: yPos,
        head: [metricsTable[0]],
        body: metricsTable.slice(1),
        theme: 'striped',
        headStyles: { fillColor: [41, 128, 185], textColor: 255 },
    });
    yPos = doc.lastAutoTable.finalY + 15;

    // 3. Strategic Case Comparison
    if (geminiData && geminiData.scenarios) {
        doc.setFontSize(16);
        doc.text('Strategic Case Comparison', 14, yPos);
        yPos += 8;

        const scenarioHeaders = ['Scenario', 'Strategic Focus', 'Target Impact', 'Risk Control'];
        const scenarioBody = geminiData.scenarios.map(s => [
            s.scenario,
            s.strategic_focus,
            s.client_impact,
            s.risk_control
        ]);

        autoTable(doc, {
            startY: yPos,
            head: [scenarioHeaders],
            body: scenarioBody,
            theme: 'grid',
            headStyles: { fillColor: [0, 51, 102], textColor: 255 },
            styles: { fontSize: 9, cellPadding: 4 },
            columnStyles: {
                0: { fontStyle: 'bold', cellWidth: 25 },
                1: { cellWidth: 'auto' },
                2: { cellWidth: 'auto' },
                3: { cellWidth: 'auto' }
            }
        });
        yPos = doc.lastAutoTable.finalY + 15;
    }

    // 4. Executive Summary
    if (geminiData && geminiData.overall_summary) {
        if (yPos > doc.internal.pageSize.getHeight() - 40) {
            doc.addPage();
            yPos = 20;
        }
        doc.setFontSize(14);
        doc.setFont(undefined, 'bold');
        doc.text('Executive Brief:', 14, yPos);
        yPos += 8;
        doc.setFont(undefined, 'normal');
        doc.setFontSize(11);
        const splitText = doc.splitTextToSize(geminiData.overall_summary, pageWidth - 28);
        doc.text(splitText, 14, yPos);
    }

    // 5. Footer
    const pageCount = doc.internal.getNumberOfPages();
    for (let i = 1; i <= pageCount; i++) {
        doc.setPage(i);
        doc.setFontSize(10);
        doc.setTextColor(150);
        doc.text(`Page ${i} of ${pageCount}`, pageWidth / 2, doc.internal.pageSize.getHeight() - 10, { align: 'center' });
    }

    // Save PDF
    doc.save(`Policy_Report_${domain}_${dateStr.replace(/\//g, '-')}.pdf`);
};
