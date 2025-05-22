import React, { useEffect, useState,} from 'react';
import { useParams, useNavigate } from 'react-router';
import { Container, Row, Col, Card, CardBody, Form, FormGroup, Label, Input, Button } from 'reactstrap';
import { toast, ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import { baseUrl } from '../../../../ConfigUrl/config';
import { getStrategyById } from '../../../../Services/Authentication';

const StrategiesClientView = () => {
    const { id } = useParams();
    const navigate = useNavigate();
    const [strategyData, setStrategyData] = useState([]);

    useEffect(() => {
        fetchStrategyData();
    }, []);

    const fetchStrategyData = async () => {
        try {
            // Fetch strategy data by ID
            const response = await getStrategyById(id);

            // Extract strategy data from the response
            setStrategyData([response]); 

            
        } catch (error) {
            toast.error('Failed to load strategy data');
        }
    };

    const placeholderImg = 'https://via.placeholder.com/150';


    const renderImage = (imgSrc, altText) => (
        <div className="image-container text-center" style={{ width: '180px', height: '140px', margin: '0 0' }}>
            <img
                style={{
                    cursor: 'pointer',
                    width: '100%',
                    height: '100%',
                    objectFit: 'cover',
                    borderRadius: '5px'
                }}
                className="img-fluid"
                src={imgSrc ? `${baseUrl}/${imgSrc}` : placeholderImg}
                alt={altText}
            />
            {!imgSrc && <p style={{ color: 'gray', marginTop: '10px' }}>No Img Found</p>}
        </div>
    );

    const handleBackClick = () => {
        navigate('/service-manage/clientstrategies');
    };

    return (
        <Container fluid>
            <ToastContainer />
            <Row className="justify-content-center">
                <Col md="10" style={{ width: '100%' }}>
                    <Card style={{ marginTop: '30px' }}>
                        <CardBody>
                            <h4 className='text-center'>Strategy Details</h4>
                            {strategyData.map((strategy) => (
                                <div key={strategy.id} className="strategy-item">
                                    <Form className="theme-form mt-3">
                                        <Row form>
                                            <Col md={6}>
                                                <FormGroup>
                                                    <Label for="strategyName">Strategy Name</Label>
                                                    <Input type="text" id="strategyName" value={strategy.name} disabled />
                                                </FormGroup>
                                            </Col>
                                            <Col md={6}>
                                                <FormGroup>
                                                    <Label for="lots">Lots</Label>
                                                    <Input type="number" id="lots" value={strategy.Lots} disabled />
                                                </FormGroup>
                                            </Col>
                                        </Row>
                                        <Row form>
                                            <Col md={6}>
                                                <FormGroup>
                                                    <Label for="segment">Segment</Label>
                                                    <Input type="text" id="segment" value={strategy.segment.name} disabled />
                                                </FormGroup>
                                            </Col>
                                            <Col md={6}>
                                                <FormGroup>
                                                    <Label for="category">Category</Label>
                                                    <Input type="text" id="category" value={strategy.category.name} disabled />
                                                </FormGroup>
                                            </Col>
                                        </Row>
                                        <Row form>
                                            <Col md={12}>
                                                <FormGroup>
                                                    <Label for="description">Description</Label>
                                                    <Input type="text" id="description" value={strategy.description} disabled />
                                                </FormGroup>
                                            </Col>
                                        </Row>
                                        <Row form>
                                            <Col md={6}>
                                                <FormGroup>
                                                    <Label for="monthlyAmount">Monthly Amount</Label>
                                                    <Input type="text" id="monthlyAmount" value={strategy.monthly_amount} disabled />
                                                </FormGroup>
                                            </Col>
                                            <Col md={6}>
                                                <FormGroup>
                                                    <Label for="quarterlyAmount">Quarterly Amount</Label>
                                                    <Input type="text" id="quarterlyAmount" value={strategy.quarterly_amount} disabled />
                                                </FormGroup>
                                            </Col>
                                            <Col md={6}>
                                                <FormGroup>
                                                    <Label for="halfYearlyAmount">Half Yearly Amount</Label>
                                                    <Input type="text" id="halfYearlyAmount" value={strategy.half_yearly_amount} disabled />
                                                </FormGroup>
                                            </Col>
                                            <Col md={6}>
                                                <FormGroup>
                                                    <Label for="yearlyAmount">Yearly Amount</Label>
                                                    <Input type="text" id="yearlyAmount" value={strategy.yearly_amount} disabled />
                                                </FormGroup>
                                            </Col>
                                        </Row>
                                        <Row form>
                                            <Col md={6}>
                                                <FormGroup>
                                                    <Label for="indicator">Indicator</Label>
                                                    {renderImage(strategy.Indicator, "Strategy Indicator")}
                                                </FormGroup>
                                            </Col>
                                            <Col md={6}>
                                                <FormGroup>
                                                    <Label for="tester">Strategy Tester</Label>
                                                    {renderImage(strategy.Strategy_Tester, "Strategy Tester")}
                                                </FormGroup>
                                            </Col>
                                            <Col md={6}>
                                                <FormGroup>
                                                    <Label for="logo">Strategy Logo</Label>
                                                    {renderImage(strategy.Strategy_Logo, "Strategy Logo")}
                                                </FormGroup>
                                            </Col>
                                        </Row>
                                    </Form>
                                </div>
                            ))}
                            <div className="text-center mt-4">
                                <Button className='search-btn-clr' onClick={handleBackClick}>
                                    Back
                                </Button>
                            </div>
                        </CardBody>
                    </Card>
                </Col>
            </Row>
        </Container>
    );
};

export default StrategiesClientView;
