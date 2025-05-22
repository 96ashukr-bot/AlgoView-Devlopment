import React, { Fragment, useState } from 'react';
import {
    Col, Card, Table, CardHeader, 
    Pagination, PaginationItem, PaginationLink, 
    Input, Button
} from 'reactstrap';
import './License.css';

const TransactionLicense = () => {
    const [licenses, setLicenses] = useState([]);
    const [currentPage, setCurrentPage] = useState(1);
    const [itemsPerPage] = useState(10);
    const [searchQuery, setSearchQuery] = useState('');

    const mockData = [
        // { clientName: 'John Doe', license: 'Enterprise', createdAt: '2024-10-12T10:00:00Z' },
        // { clientName: 'Jane Smith', license: 'Standard', createdAt: '2024-10-10T14:30:00Z' },
        // { clientName: 'Alex Johnson', license: 'Premium', createdAt: '2024-10-09T09:15:00Z' },
    ];

    const filteredLicenses = mockData.filter(item =>
        item.clientName.toLowerCase().includes(searchQuery.toLowerCase()) ||
        item.license.toLowerCase().includes(searchQuery.toLowerCase())
    );

    const indexOfLastLicense = currentPage * itemsPerPage;
    const indexOfFirstLicense = indexOfLastLicense - itemsPerPage;
    const currentLicenses = filteredLicenses.slice(indexOfFirstLicense, indexOfLastLicense);

    const totalPages = Math.ceil(filteredLicenses.length / itemsPerPage);

    return (
        <Fragment>
            <Col sm="12">
                <Card>
                    <CardHeader>
                        <div className="d-flex justify-content-between align-items-center">
                            <div>
                                {/* <H3>Transaction License</H3> */}
                                <h3>Transaction License</h3>
                                {/* <span>{"Below is the list of licenses along with their details."}</span> */}
                            </div>
                            <div>
                                <Input
                                    type="text"
                                    placeholder="Search..."
                                    value={searchQuery}
                                    onChange={(e) => setSearchQuery(e.target.value)}
                                    style={{ width: '200px', display: 'inline-block', marginRight: '10px' }}
                                />
                                <Button className='search-btn-clr'>Search</Button>
                            </div>
                        </div>
                    </CardHeader>
                    <div className="card-block row">
                        <Col sm="12" lg="12" xl="12">
                            <div className="table-responsive-sm">
                                <Table>
                                    <thead>
                                        <tr>
                                            <th style={{backgroundColor:'#283F7B',color:'white'}}>Sr.No</th>
                                            <th style={{backgroundColor:'#283F7B',color:'white'}}>Client Name</th>
                                            <th style={{backgroundColor:'#283F7B',color:'white'}}>License</th>
                                            <th style={{backgroundColor:'#283F7B',color:'white'}}>Created At</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {currentLicenses.map((license, index) => (
                                            <tr key={index}>
                                                <td>{indexOfFirstLicense + index + 1}</td>
                                                <td>{license.clientName}</td>
                                                <td>{license.license}</td>
                                                <td>{new Date(license.createdAt).toLocaleString()}</td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </Table>
                            </div>

                            {/* Pagination */}
                            <div className="d-flex justify-content-end custom-pagi-style">
                                <Pagination>
                                    <PaginationItem disabled={currentPage === 1}>
                                        <PaginationLink onClick={() => setCurrentPage(currentPage - 1)}>
                                            Previous
                                        </PaginationLink>
                                    </PaginationItem>
                                    {[...Array(totalPages)].map((_, index) => (
                                        <PaginationItem key={index} active={index + 1 === currentPage}>
                                            <PaginationLink onClick={() => setCurrentPage(index + 1)}>
                                                {index + 1}
                                            </PaginationLink>
                                        </PaginationItem>
                                    ))}
                                    <PaginationItem disabled={currentPage === totalPages}>
                                        <PaginationLink onClick={() => setCurrentPage(currentPage + 1)}>
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

export default TransactionLicense;
