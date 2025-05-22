import Swal from 'sweetalert2';
import React, { Fragment, useState, useEffect } from 'react';
import { Col, Card, CardHeader, Input, Button, FormGroup, Label, Pagination, PaginationItem, PaginationLink } from 'reactstrap';
import { H3 } from '../../../../AbstractElements';
import { useNavigate, useParams } from 'react-router-dom';
import { getClients, getStrategiesById, updateStrategyClientList } from '../../../../Services/Authentication';

const UpdateStrategies = () => {
    const { id } = useParams();
    const [clients, setClients] = useState([]);
    const [selectedClients, setSelectedClients] = useState({});
    const [searchQuery, setSearchQuery] = useState('');
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [currentPage, setCurrentPage] = useState(1);
    const [totalPages, setTotalPages] = useState([]);
    const [clientsPerPage] = useState(10);
    const [itemsPerPage] = useState(10);
    const pagesPerBatch = 4;
    const [pageBatch, setPageBatch] = useState(0);
    const navigate = useNavigate();

    useEffect(() => {
        fetchClients();
        fetchStrategyDetails();
    }, [id, currentPage]);

    const fetchClients = async () => {
        try {
            setLoading(true);
            const response = await getClients(currentPage);

            if (response.results && response.results.length > 0) {
                setClients(response.results);
                setTotalPages(Math.ceil(response.count / itemsPerPage));
            } else {
                setClients([]);
            }
        } catch (err) {
            console.error("Error fetching data:", err);
            setError("Failed to load data.");
        } finally {
            setLoading(false);
        }
    };

    const fetchStrategyDetails = async () => {
        try {
            const strategyDetails = await getStrategiesById(id);
            if (strategyDetails && strategyDetails.clients) {
                // Map `is_using_strategy` to `selectedClients`
                const clientSelections = strategyDetails.clients.reduce((acc, client) => {
                    acc[client.client_id] = client.is_using_strategy;
                    return acc;
                }, {});
                setSelectedClients(clientSelections);
            }
        } catch (error) {
            console.error("Error fetching strategy details:", error);
            setError("Failed to load strategy details.");
        }
    };
    
    const handleCheckboxChange = (clientId) => {
        setSelectedClients((prev) => ({
            ...prev,
            [clientId]: !prev[clientId],
        }));
    };

    const handleAddClick = async () => {
        try {
            const selectedClientIds = Object.keys(selectedClients)
                .filter((clientId) => selectedClients[clientId] && clientId !== "null" && clientId !== "undefined")
                .map(Number); // Ensure all client IDs are numbers
    
            console.log('Updating Strategy ID:', id);
            console.log('Selected Clients Payload:', selectedClientIds);
    
            await updateStrategyClientList(id, selectedClientIds);
    
            Swal.fire({
                icon: 'success',
                title: 'Success!',
                text: 'Clients updated successfully!',
                confirmButtonText: 'OK',
            }).then(() => navigate('/service-manage/strategies'));
        } catch (error) {
            console.error('Error updating strategy clients:', error);
    
            Swal.fire({
                icon: 'error',
                title: 'Error!',
                text: 'Failed to update clients.',
                confirmButtonText: 'Try Again',
            });
        }
    };
    
    const filteredClients = clients.filter((client) =>
        client.fullName.toLowerCase().includes(searchQuery.toLowerCase())
    );

    const indexOfLastClient = currentPage * clientsPerPage;
    const indexOfFirstClient = indexOfLastClient - clientsPerPage;
    const currentClients = filteredClients;

    if (currentPage === 1 && filteredClients.length > itemsPerPage) {
        const extraItem = filteredClients[filteredClients.length - 1];
        currentClients = [extraItem, ...currentClients.slice(0, itemsPerPage - 1)];
    }

    const handlePreviousBatch = () => {
        if (pageBatch > 0) setPageBatch(pageBatch - 1);
    };

    const handleNextBatch = () => {
        const maxBatch = Math.ceil(totalPages / pagesPerBatch) - 1;
        if (pageBatch < maxBatch) setPageBatch(pageBatch + 1);
    };

    const handlePageChange = (page) => {
        setCurrentPage(page);
    };

    const handlePrevious = () => {
        if (currentPage > 1) setCurrentPage(currentPage - 1);
    };

    const handleNext = () => {
        if (currentPage < totalPages) setCurrentPage(currentPage + 1);
    };

    const startPage = pageBatch * pagesPerBatch + 1;
    const endPage = Math.min(startPage + pagesPerBatch - 1, totalPages);
    const pages = Array.from({ length: endPage - startPage + 1 }, (_, i) => startPage + i);

    return (
        <Fragment>
            <Col sm="12">
                <Card>
                    <CardHeader>
                        <div className="d-flex justify-content-between align-items-center custom-responsive-style">
                            <div>
                                <H3>Client List</H3>
                            </div>
                            <div className="custom-responsive-style-search">
                                <Input
                                    type="text"
                                    placeholder="Search..."
                                    value={searchQuery}
                                    onChange={(e) => setSearchQuery(e.target.value)}
                                    style={{ width: '200px', display: 'inline-block', marginRight: '10px' }}
                                />
                                <Button className="search-btn-clr">Search</Button>
                            </div>
                        </div>
                    </CardHeader>

                    <div className="card-block row p-3">
                        <Col sm="12" lg="12" xl="12">
                            {currentClients.map((client) => (
                                <FormGroup key={client.id} check className="mb-2">
                                    <Label check style={{ display: 'inline-flex' }}>
                                        <input
                                            type="checkbox"
                                            style={{
                                                marginLeft: '20px',
                                                marginRight: '10px',
                                                transform: 'scale(1.3)',
                                                transformOrigin: 'center',
                                            }}
                                            checked={selectedClients[client.id] || false}
                                            onChange={() => handleCheckboxChange(client.id)}
                                        />
                                        {client.fullName}
                                    </Label>
                                </FormGroup>
                            ))}
                            <div className="d-flex justify-content-start mt-4" style={{ padding: '10px' }}>
                                <Button className="me-2 search-btn-clr" onClick={handleAddClick}>
                                    Add
                                </Button>
                                <Button color="danger" onClick={() => navigate('/service-manage/strategies')}>
                                    Cancel
                                </Button>
                            </div>
                            <div className="d-flex justify-content-end">
                                <Pagination>
                                    {/* Previous button */}
                                    <PaginationItem disabled={currentPage === 1}>
                                        <PaginationLink previous onClick={handlePrevious}>
                                            Previous
                                        </PaginationLink>
                                    </PaginationItem>

                                    {/* '<' arrow */}
                                    {pageBatch > 0 && (
                                        <PaginationItem>
                                            <PaginationLink onClick={handlePreviousBatch}>&lt;</PaginationLink>
                                        </PaginationItem>
                                    )}

                                    {/* Page numbers */}
                                    {pages.map((page) => (
                                        <PaginationItem active={page === currentPage} key={page}>
                                            <PaginationLink onClick={() => handlePageChange(page)}>{page}</PaginationLink>
                                        </PaginationItem>
                                    ))}

                                    {/* '>' arrow */}
                                    {endPage < totalPages && (
                                        <PaginationItem>
                                            <PaginationLink onClick={handleNextBatch}>&gt;</PaginationLink>
                                        </PaginationItem>
                                    )}

                                    {/* Next button */}
                                    <PaginationItem disabled={currentPage === totalPages}>
                                        <PaginationLink next onClick={handleNext}>
                                            Next
                                        </PaginationLink>
                                    </PaginationItem>
                                </Pagination>
                            </div>
                        </Col>
                    </div>
                </Card>
            </Col>
        </Fragment>
    );
};

export default UpdateStrategies;
