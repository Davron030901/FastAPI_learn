import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import axios from 'axios';

interface Plate {
  id: number;
  plate_number: string;
  description: string;
  deadline: string;
  highest_bid: number;
  is_active: boolean;
}

function PlateList() {
  const [plates, setPlates] = useState<Plate[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchPlates = async () => {
      try {
        const response = await axios.get('http://localhost:8000/plates', {
          headers: {
            Authorization: `Bearer ${localStorage.getItem('token')}`,
          },
        });
        setPlates(response.data);
      } catch (err) {
        console.error('Error fetching plates:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchPlates();
  }, []);

  if (loading) {
    return <div>Loading...</div>;
  }

  return (
    <div>
      <h2 className="text-2xl font-bold mb-4">Available Plates</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {plates.map((plate) => (
          <Link
            key={plate.id}
            to={`/plates/${plate.id}`}
            className="border p-4 rounded hover:shadow-lg"
          >
            <h3 className="text-xl font-bold">{plate.plate_number}</h3>
            <p className="text-gray-600">{plate.description}</p>
            <p className="text-gray-600">
              Deadline: {new Date(plate.deadline).toLocaleDateString()}
            </p>
            <p className="text-gray-600">
              Highest Bid: ${plate.highest_bid.toFixed(2)}
            </p>
            <span
              className={`inline-block px-2 py-1 rounded ${
                plate.is_active
                  ? 'bg-green-500 text-white'
                  : 'bg-red-500 text-white'
              }`}
            >
              {plate.is_active ? 'Active' : 'Closed'}
            </span>
          </Link>
        ))}
      </div>
    </div>
  );
}

export default PlateList;