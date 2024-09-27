import React, { Fragment, useEffect, useState } from 'react';
import { Col, Card, Table, CardHeader } from 'reactstrap';
import { H3 } from '../../../AbstractElements';

const Signals = () => {
    const [signals, setSignals] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchSignals = async () => {
            try {
                const response = await fetch('http://127.0.0.1:8000/order-logs-list');
                const result = await response.json();
                if (result.status === 'success') {
                    setSignals(result.data);
                } else {
                    console.error('Error fetching signals:', result.message);
                }
            } catch (error) {
                console.error('Error fetching signals:', error);
            } finally {
                setLoading(false);
            }
        };
        fetchSignals();
    }, []);

    if (loading) {
        return <div>Loading...</div>; 
    }

    return (
        <Fragment>
            <Col sm="12">
                <Card>
                    <CardHeader>
                        <H3>Signals</H3>
                        <span>{"Below is the list of signals along with their details."}</span>
                    </CardHeader>
                    <div className="card-block row">
                        <Col sm="12" lg="12" xl="12">
                            <Table className="table-responsive-sm">
                                <thead>
                                    <tr>
                                        <th>S.No.</th>
                                        <th>Signal Time</th>
                                        <th>Order Type</th>
                                        <th>Symbol</th>
                                        <th>Price</th>
                                        <th>Strategy</th>
                                        <th>Created At</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {signals.map((signal, index) => (
                                        <tr key={index}>
                                            <td>{index + 1}</td>
                                            <td>{new Date(signal.signal_time).toLocaleString()}</td>
                                            <td>{signal.order_type}</td>
                                            <td>{signal.symbol}</td>
                                            <td>{signal.price}</td>
                                            <td>{signal.strategy}</td>
                                            <td>{new Date(signal.created_at).toLocaleString()}</td>
                                        </tr>
                                    ))}
                                </tbody>
                            </Table>
                        </Col>
                    </div>
                </Card>
            </Col>
        </Fragment>
    );
};

export default Signals;
