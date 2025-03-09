import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import axios from 'axios';

interface Bid {
  id: number;
  amount: number;
  created_at: string;
  user_id: number;
}

interface Plate {
  id: number;
  plate_number: string;
  description: string;
  deadline: string;
  highest_bid: number;
  is_active: boolean;
  bids: Bid[];
}

function PlateDetail() {
  const { id } = useParams();
  const [plate, setPlate] = useState<Plate | null>(null);
  const [bidAmount, setBidAmount] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchPlate = async () => {
      try {
        const response = await axios.get(`http://localhost:8000/plates/${id}`, {
          headers: {
            Authorization: `Bearer ${localStorage.getItem('token')}`,
          },
        });
        setPlate(response.data);
      } catch (err) {
        console.error('Error fetching plate:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchPlate();
  }, [id]);

  const handleBid = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await axios.post(
        'http://localhost:8000/bids',
        {
          plate_id: id,
          amount: parseFloat(bidAmount),
        },
        {
          headers: {
            Authorization: `Bearer ${localStorage.getItem('token')}`,
          },
        }
      );
      // Refresh plate data after successful bid
      window.location.reload();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Error placing bid');
    }
  };

  if (loading) {
    return <div>Loading...</div>;
  }

  if (!plate) {
    return <div>Plate not found</div>;
  }

  return (
    <div className="max-w-2xl mx-auto">
      <h2 className="text-2xl font-bold mb-4">{plate.plate_number}</h2>
      <div className="mb-4">
        <p className="text-gray-600">{plate.description}</p>
        <p className="text-gray-600">
          Deadline: {new Date(plate.deadline).toLocaleDateString()}
        </p>
        <p className="text-gray-600">
          Highest Bid: ${plate.highest_bid.toFixed(2)}
        </p>
        <span
          className={`inline-block px-2 py-1 rounded ${
            plate.is_active ? 'bg-green-500 text-white' : 'bg-red-500 text-white'
          }`}
        >
          {plate.is_active ? 'Active' : 'Closed'}
        </span>
      </div>

      {plate.is_active && (
        <form onSubmit={handleBid} className="mb-8">
          <div className="mb-4">
            <label className="block mb-2">Place a Bid</label>
            <input
              type="number"
              step="0.01"
              value={bidAmount}
              onChange={(e) => setBidAmount(e.target.value)}
              className="w-full border p-2"
              required
            />
          </div>
          {error && <div className="text-red-500 mb-4">{error}</div>}
          <button
            type="submit"
            className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
          >
            Place Bid
          </button>
        </form>
      )}

      <div>
        <h3 className="text-xl font-bold mb-4">Bid History</h3>
        <div className="space-y-4">
          {plate.bids.map((bid) => (
            <div key={bid.id} className="border p-4 rounded">
              <p className="font-bold">${bid.amount.toFixed(2)}</p>
              <p className="text-gray-600">
                {new Date(bid.created_at).toLocaleString()}
              </p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export default PlateDetail;