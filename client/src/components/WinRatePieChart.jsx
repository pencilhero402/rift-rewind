import { Pie } from 'react-chartjs-2';
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from 'chart.js';

ChartJS.register(ArcElement, Tooltip, Legend);

const WinRatePieChart = ({ winrate }) => {
  const data = {
    labels: ['Wins', 'Losses'],
    datasets: [
      {
        data: [winrate * 100, (1 - winrate) * 100],
        backgroundColor: ['blue', 'lightgray'],
        borderWidth: 1,
        cutout: '70%', // makes it a donut
      },
    ],
  };

  const options = {
    plugins: {
      legend: { display: false },
    },
    responsive: true,
    maintainAspectRatio: false,
  };

  // Custom plugin to draw center text
  const centerTextPlugin = {
    id: 'centerText',
    beforeDraw: (chart) => {
      const { width, height, ctx } = chart;
      ctx.save();
      const text = `${(winrate * 100).toFixed(1)}%`;
      ctx.fillStyle = 'white';
      ctx.font = 'bold 24px Arial';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText(text, width / 2, height / 2);
      ctx.restore();
    },
  };

  return <Pie data={data} options={options} plugins={[centerTextPlugin]} />;
};

export default WinRatePieChart;
