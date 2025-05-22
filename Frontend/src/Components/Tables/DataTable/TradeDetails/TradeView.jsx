import React, { Fragment, useState, useEffect } from 'react';
import {
    Col, Card, Table, CardHeader, Pagination, PaginationItem, PaginationLink,
    Input, Button, Form, FormGroup, Label, Row
} from 'reactstrap';
import * as XLSX from 'xlsx';
import { saveAs } from 'file-saver';
import './TradeDetails.css';
import { RotatingLines } from 'react-loader-spinner';
import { getClientTradeHistory, getTradeStrategy, getBroker, TradeViewSearch } from '../../../../Services/Authentication';
import { H3 } from '../../../../AbstractElements';
import { FaArrowUp, FaArrowDown } from 'react-icons/fa';

const TradeView = () => {
    const [currentPage, setCurrentPage] = useState(1);
    const [itemsPerPage, setItemsPerPage] = useState(10);
    const [error, setError] = useState(null);
    const [totalPages, setTotalPages] = useState([]);
    const [strategies, setStrategies] = useState([]);
    const [selectedClientType, setSelectedClientType] = useState('');
    const [searchQuery, setSearchQuery] = useState('');
    const [formData, setFormData] = useState({
        fromDate: '',
        toDate: '',
        broker: '',
        orderStatus: '',
        indexSymbol: '',
        strategy: '',
    });
    const [indexSymbols, setIndexSymbols] = useState([]);
    const [brokers, setBrokers] = useState([]);
    const [sortConfig, setSortConfig] = useState({ key: '', direction: '' });
    const [clientTradeHistory, setClientTradeHistory] = useState([]);
    const [loading, setLoading] = useState(false);
    const [isMobile, setIsMobile] = useState(false);
    const [pageBatch, setPageBatch] = useState(0);

    const staticIndexSymbols = [
        'BANKNIFTY',
        'NIFTY',
        'MIDCPNIFTY',
        'FINNIFTY',
        'SENSEX'
    ];

    const staticOrderStatus = [
        'open',
        'failed',
        'rejected',
        'complete',
        'completed',
        'errors',
        'unauthorized',
        'transit'
    ];

    useEffect(() => {
        if (searchQuery) {
            handleSearch();
        } else {
            fetchClientTradeHistory();
        }
        fetchTradeStrategies();
        fetchBrokers();

        const handleResize = () => {
            setIsMobile(window.innerWidth <= 768);
        };

        handleResize();
        window.addEventListener('resize', handleResize);

        return () => window.removeEventListener('resize', handleResize);

    }, [currentPage, itemsPerPage, formData.fromDate, formData.toDate, formData.broker, formData.orderStatus ,formData.indexSymbol, formData.strategy, searchQuery]);

    const pagesPerBatch = isMobile ? 2 : 4;

    const fetchClientTradeHistory = async () => {
        try {
            setLoading(true);

            // Get today's date in YYYY-MM-DD format
            const today = new Date().toISOString().split('T')[0];

            // Determine the dates to use for the API call
            const fromDate = formData.fromDate || today; // Use fromDate if provided, otherwise default to today
            const toDate = formData.toDate || today; // Use toDate if provided, otherwise default to today

            // Fetch data for the specified date range
            let response = await getClientTradeHistory(currentPage, itemsPerPage, fromDate, toDate, formData.broker, formData.orderStatus ,formData.indexSymbol, formData.strategy, searchQuery);

            // If no data is found for the specified date range and no filters are applied, fall back to the last available date
            // if ((!response.results || response.results.length === 0) && !formData.fromDate && !formData.toDate) {
            //     const lastAvailableDateResponse = await getClientTradeHistory(currentPage, itemsPerPage, '', '', formData.broker, formData.indexSymbol, formData.strategy, searchQuery);

            //     if (lastAvailableDateResponse.results && lastAvailableDateResponse.results.length > 0) {
            //         // Sort the results by date to get the last available date
            //         const sortedResults = lastAvailableDateResponse.results.sort((a, b) => new Date(b.SignalEntry_time) - new Date(a.SignalEntry_time));
            //         const lastAvailableDate = sortedResults[0].SignalEntry_time.split('T')[0];

            //         // Fetch data for the last available date
            //         response = await getClientTradeHistory(currentPage, itemsPerPage, lastAvailableDate, lastAvailableDate, formData.broker, formData.indexSymbol, formData.strategy, searchQuery);
            //     }
            // }

            if (response.results && response.results.length > 0) {
                setClientTradeHistory(response.results);
                setTotalPages(Math.ceil(response.count / itemsPerPage));
            } else {
                setClientTradeHistory([]);
            }
        } catch (err) {
            console.error("Error fetching data:", err);
            setError("Failed to load data.");
        } finally {
            setLoading(false);
        }
    };

    const handleSearch = async () => {
        try {
            setLoading(true);
            const response = await TradeViewSearch(searchQuery,itemsPerPage);
            if (response?.results?.length > 0) {
                setClientTradeHistory(response.results);
            } else {
                setClientTradeHistory([]);
            }
        } catch (error) {
            console.error('Error during search:', error);
            setError("Search failed.");
        } finally {
            setLoading(false);
        }
    };

    const calculateTotal = (exitPrice, exitQty, entryPrice, entryQty, orderStatus) => {
        if (orderStatus === 'complete' && exitPrice !== null && entryPrice !== null) {
            const total = (exitPrice * exitQty) - (entryPrice * entryQty);
            return total.toFixed(2);
        }
        return null;
    };

    const fetchTradeStrategies = async () => {
        try {
            const response = await getTradeStrategy();
            if (response.strategies && response.strategies.length > 0) {
                setStrategies(response.strategies);
            } else {
                setStrategies([]);
            }
        } catch (err) {
            console.error("Error fetching strategies:", err);
            setError("Failed to load strategies.");
        }
    };

    const fetchBrokers = async () => {
        try {
            const response = await getBroker();
            setBrokers(response && Array.isArray(response) ? response : []);
        } catch (error) {
            console.error('Failed to load brokers.');
        }
    };

    const handleReset = () => {
        setSelectedClientType('');
        setFormData({
            fromDate: '',
            toDate: '',
            broker: '',
            orderStatus: '',
            indexSymbol: '',
            strategy: '',
        });
        setSearchQuery('');
    };

    const handleExportExcel = () => {
        // Map the client trade history data to a simpler structure
        const data = clientTradeHistory.map((signal, index) => ({
            'S. No.': index + 1,
            'Signal Entry Time': signal.SignalEntry_time || '-',
            'Signal Exit Time': signal.SignalExit_time || '-',
            Symbol: signal.trading_symbol || '-',
            Strategy: signal.strategy || '-',
            'Entry Type': signal.Entry_type || '-',
            'Entry Qty': signal.EntryQty || '-',
            'Exit Qty': signal.ExitQty || '-',
            'Entry Price': signal.Entry_Price !== null ? signal.Entry_Price : '-',
            'Exit Price': signal.Exit_Price !== null ? signal.Exit_Price : '-',
            Total: signal.Total || '-',
        }));

        const worksheet = XLSX.utils.json_to_sheet(data);
        const workbook = XLSX.utils.book_new();
        XLSX.utils.book_append_sheet(workbook, worksheet, 'Trade History');

        // Get current date and time in the format "26/12/2024 11:35:03"
        const now = new Date();
        const formattedDate = now.toLocaleDateString('en-GB').replace(/\//g, '-'); // Format date as "dd-MM-yyyy"
        const formattedTime = now
            .toLocaleTimeString('en-GB', { hour12: false })
            .replace(/:/g, '-'); // Format time as "HH-mm-ss"

        // Create Excel file and trigger download
        const excelBuffer = XLSX.write(workbook, { bookType: 'xlsx', type: 'array' });
        const blob = new Blob([excelBuffer], { type: 'application/octet-stream' });
        saveAs(blob, `Trade_History_${formattedDate}_${formattedTime}.xlsx`);
    };


    const handleInputChange = (e) => {
        const { name, value } = e.target;
        setFormData({ ...formData, [name]: value });
    };

    const formatDateTime = (dateTime) => {
        if (!dateTime) return '-';
        const date = new Date(dateTime);
        const day = String(date.getDate()).padStart(2, '0');
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const year = date.getFullYear();
        const hours = String(date.getHours()).padStart(2, '0');
        const minutes = String(date.getMinutes()).padStart(2, '0');
        const seconds = String(date.getSeconds()).padStart(2, '0');
        return `${day}/${month}/${year} ${hours}:${minutes}:${seconds}`;
    };

    const handleSort = (key) => {
        let direction = 'asc';
        if (sortConfig.key === key && sortConfig.direction === 'asc') {
            direction = 'desc';
        }
        setSortConfig({ key, direction });

        const sortedSignals = [...clientTradeHistory].sort((a, b) => {
            if (a[key] < b[key]) return direction === 'asc' ? -1 : 1;
            if (a[key] > b[key]) return direction === 'asc' ? 1 : -1;
            return 0;
        });
        setClientTradeHistory(sortedSignals);
    };

    const filteredSignals = clientTradeHistory.filter(signal => {
        const signalDate = signal.SignalEntry_time ? new Date(signal.SignalEntry_time) : null;
        const signalExitDate = signal.SignalExit_time ? new Date(signal.SignalExit_time) : null;
        const fromDate = new Date(formData.fromDate);
        const toDate = new Date(formData.toDate);

        // Adjust toDate to include the entire day
        toDate.setHours(23, 59, 59, 999); // Set to the end of the day

        const searchLower = searchQuery.toLowerCase();

        const isWithinDateRange = (!formData.fromDate || signalDate >= fromDate) &&
            (!formData.toDate || signalDate <= toDate);

        // Compare with the broker name from the dropdown
        const matchesBroker = !formData.broker || (signal.broker && signal.broker.toLowerCase() === formData.broker.toLowerCase());
        const matchesOrderStatus = !formData.orderStatus || (signal.order_status && signal.order_status.toLowerCase() === formData.orderStatus.toLowerCase());
        const matchesIndexSymbol = !formData.indexSymbol || signal.Index_Symbol === formData.indexSymbol;
        const matchesStrategy = !formData.strategy || (signal.strategy && signal.strategy.toLowerCase() === formData.strategy.toLowerCase());

        return (
            isWithinDateRange &&
            matchesBroker &&
            matchesOrderStatus &&
            matchesIndexSymbol &&
            matchesStrategy &&
            (
                (signalDate && signalDate.toLocaleDateString('en-GB').includes(searchLower)) ||
                (signalExitDate && signalExitDate.toLocaleDateString('en-GB').includes(searchLower)) ||
                (signal.trading_symbol && signal.trading_symbol.toLowerCase().includes(searchLower)) ||
                (signal.strategy && signal.strategy.toLowerCase().includes(searchLower)) ||
                (signal.GroupService && signal.GroupService.toLowerCase().includes(searchLower)) ||
                // (signal.order_status && String(signal.order_status).toLowerCase().includes(searchLower)) ||
                (signal.Entry_type && String(signal.Entry_type).toLowerCase().includes(searchLower)) ||
                (signal.client?.full_name && signal.client.full_name.toLowerCase().includes(searchLower)) ||
                (signal.broker && signal.broker.toLowerCase().includes(searchLower))
            )
        );
    });

    const indexOfLastSignal = currentPage * itemsPerPage;
    const indexOfFirstSignal = indexOfLastSignal - itemsPerPage;

    let currentSignals = filteredSignals;

    if (currentPage === 1 && filteredSignals.length > itemsPerPage) {
        const extraItem = filteredSignals[filteredSignals.length - 1];
        currentSignals = [extraItem, ...currentSignals.slice(0, itemsPerPage - 1)];
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
                                <H3>Trade View</H3>
                            </div>
                            <div className='custom-responsive-style-search'>
                                <Input
                                    type="text"
                                    placeholder="Search..."
                                    value={searchQuery}
                                    onChange={(e) => setSearchQuery(e.target.value)}
                                    onKeyDown={(e) => {
                                        if (e.key === 'Enter') {
                                            handleSearch();
                                        }
                                    }}
                                    style={{ width: '200px', display: 'inline-block', marginRight: '10px' }}
                                />
                                <Button className='search-btn-clr' onClick={handleSearch}>Search</Button>
                            </div>
                        </div>

                        {/* Form Row with multiple filters */}
                        <Form className="mt-3">
                            <Row form>
                                <Col md={2}>
                                    <FormGroup>
                                        <Label for="fromDate">From Date</Label>
                                        <Input
                                            type="date"
                                            name="fromDate"
                                            id="fromDate"
                                            value={formData.fromDate}
                                            onChange={handleInputChange}
                                        />
                                    </FormGroup>
                                </Col>
                                <Col md={2}>
                                    <FormGroup>
                                        <Label for="toDate">To Date</Label>
                                        <Input
                                            type="date"
                                            name="toDate"
                                            id="toDate"
                                            value={formData.toDate}
                                            onChange={handleInputChange}
                                        />
                                    </FormGroup>
                                </Col>
                                <Col md={2}>
                                    <FormGroup>
                                        <Label for="broker">Broker</Label>
                                        <Input
                                            type="select"
                                            name="broker"
                                            id="broker"
                                            value={formData.broker}
                                            onChange={handleInputChange}
                                        >
                                            <option value="">All</option>
                                            {brokers.map((broker) => (
                                                <option key={broker.id} value={broker.broker_name}>{broker.broker_name}</option>
                                            ))}
                                        </Input>
                                    </FormGroup>
                                </Col>
                                <Col md={2}>
                                    <FormGroup>
                                        <Label for="orderStatus">Order Status</Label>
                                        <Input
                                            type="select"
                                            name="orderStatus"
                                            id="orderStatus"
                                            value={formData.orderStatus}
                                            onChange={handleInputChange}
                                        >
                                            <option value="">All</option>
                                            {staticOrderStatus.map((order,index) => (
                                                <option key={index} value={order}>{order}</option>
                                            ))}
                                        </Input>
                                    </FormGroup>
                                </Col>
                                <Col md={2}>
                                    <FormGroup>
                                        <Label for="strategy">Strategy</Label>
                                        <Input
                                            type="select"
                                            name="strategy"
                                            id="strategy"
                                            value={formData.strategy}
                                            onChange={handleInputChange}
                                        >
                                            <option value="">All</option>
                                            {strategies.map((strategy, index) => (
                                                <option key={index} value={strategy}>{strategy}</option>
                                            ))}
                                        </Input>
                                    </FormGroup>
                                </Col>
                                <Col md={2}>
                                    <FormGroup>
                                        <Label for="indexSymbol">Index Symbol</Label>
                                        <Input
                                            type="select"
                                            name="indexSymbol"
                                            id="indexSymbol"
                                            value={formData.indexSymbol}
                                            onChange={handleInputChange}
                                        >
                                            <option value="">All</option>
                                            {staticIndexSymbols.map((symbol, index) => (
                                                <option key={index} value={symbol}>{symbol}</option>
                                            ))}
                                        </Input>
                                    </FormGroup>
                                </Col>
                                <Col md={2} className="mt-4 d-flex gap-2">
                                    <Button className='search-btn-clr' onClick={() => handleReset()} style={{ height: '40px' }}>
                                        Reset
                                    </Button>
                                    <Button className='search-btn-clr text-nowrap' onClick={() => handleExportExcel()} style={{ height: '40px' }}>
                                        Export Excel
                                    </Button>
                                </Col>
                            </Row>
                        </Form>
                    </CardHeader>

                    <div className="card-block row" style={{ height: '100%' }}>
                        <Col sm="12" lg="12" xl="12" style={{ height: '100%' }}>
                            <div className="table-responsive" style={{ height: '100%' }}>
                                <Table>
                                    <thead>
                                        <tr>
                                            <th className="custom-col-design">S.No.</th>
                                            <th onClick={() => handleSort('SignalEntry_time')} className="custom-col-design">
                                                Signal Entry Time
                                                <FaArrowUp className="sort-arrow-left" />
                                                <FaArrowDown className="sort-arrow-right" />
                                            </th>
                                            <th onClick={() => handleSort('SignalExit_time')} className="custom-col-design">
                                                Signal Exit Time
                                                <FaArrowUp className="sort-arrow-left" />
                                                <FaArrowDown className="sort-arrow-right" />
                                            </th>
                                            <th onClick={() => handleSort('trading_symbol')} className="custom-col-design">
                                                Trading Symbol
                                                <FaArrowUp className="sort-arrow-left" />
                                                <FaArrowDown className="sort-arrow-right" />
                                            </th>
                                            <th onClick={() => handleSort('Index_Symbol')} className='custom-col-design'>Index Symbol
                                                <FaArrowUp className="sort-arrow-left" />
                                                <FaArrowDown className="sort-arrow-right" />
                                            </th>
                                            <th onClick={() => handleSort('GroupService')} className='custom-col-design'>Group Service
                                                <FaArrowUp className="sort-arrow-left" />
                                                <FaArrowDown className="sort-arrow-right" />
                                            </th>
                                            {/* <th onClick={() => handleSort('strategy')} className="custom-col-design">
                                                Strategy
                                                <FaArrowUp className="sort-arrow-left" />
                                                <FaArrowDown className="sort-arrow-right" />
                                            </th> */}
                                            <th onClick={() => handleSort('broker')} className="custom-col-design">
                                                Broker
                                                <FaArrowUp className="sort-arrow-left" />
                                                <FaArrowDown className="sort-arrow-right" />
                                            </th>
                                            <th onClick={() => handleSort('Entry_type')} className="custom-col-design">
                                                Entry Type
                                                <FaArrowUp className="sort-arrow-left" />
                                                <FaArrowDown className="sort-arrow-right" />
                                            </th>
                                            <th onClick={() => handleSort('Exit_type')} className='custom-col-design'>Exit Type
                                                <FaArrowUp className="sort-arrow-left" />
                                                <FaArrowDown className="sort-arrow-right" />
                                            </th>
                                            <th onClick={() => handleSort('EntryQty')} className="custom-col-design">
                                                Entry Qty
                                                <FaArrowUp className="sort-arrow-left" />
                                                <FaArrowDown className="sort-arrow-right" />
                                            </th>
                                            <th onClick={() => handleSort('ExitQty')} className="custom-col-design">
                                                Exit Qty
                                                <FaArrowUp className="sort-arrow-left" />
                                                <FaArrowDown className="sort-arrow-right" />
                                            </th>
                                            <th onClick={() => handleSort('Entry_Price')} className="custom-col-design">
                                                Entry Price
                                                <FaArrowUp className="sort-arrow-left" />
                                                <FaArrowDown className="sort-arrow-right" />
                                            </th>
                                            <th onClick={() => handleSort('Exit_Price')} className="custom-col-design">
                                                Exit Price
                                                <FaArrowUp className="sort-arrow-left" />
                                                <FaArrowDown className="sort-arrow-right" />
                                            </th>
                                            <th onClick={() => handleSort('Total')} className="custom-col-design">
                                                Total
                                                <FaArrowUp className="sort-arrow-left" />
                                                <FaArrowDown className="sort-arrow-right" />
                                            </th>
                                            <th onClick={() => handleSort('order_status')} className='custom-col-design'>Order Status
                                                <FaArrowUp className="sort-arrow-left" />
                                                <FaArrowDown className="sort-arrow-right" />
                                            </th>
                                            <th onClick={() => handleSort('full_name')} className='custom-col-design'>Client Name
                                                <FaArrowUp className="sort-arrow-left" />
                                                <FaArrowDown className="sort-arrow-right" />
                                            </th>
                                            <th onClick={() => handleSort('failure_reason')} className='custom-col-design'>Failure Reason
                                            </th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {loading ? (
                                            <tr>
                                                <td colSpan="9" style={{ textAlign: 'center', height: '100px' }}>
                                                    <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%' }}>
                                                        <RotatingLines
                                                            strokeColor="#283F7B"
                                                            strokeWidth="4"
                                                            animationDuration="0.75"
                                                            width="50"
                                                            visible={true}
                                                        />
                                                    </div>
                                                </td>
                                            </tr>
                                        ) : currentSignals.length > 0 ? (
                                            currentSignals.map((signal, index) => {
                                                const total = calculateTotal(signal.Exit_Price, signal.ExitQty, signal.Entry_Price, signal.EntryQty, signal.order_status);
                                                const totalValue = total !== null ? parseFloat(total) : null;
                                                return (
                                                    <tr key={signal.id}>
                                                        <td>{indexOfFirstSignal + index + 1}</td>
                                                        <td>{formatDateTime(signal.SignalEntry_time)}</td>
                                                        <td>{formatDateTime(signal.SignalExit_time)}</td>
                                                        <td>{signal.trading_symbol || '-'}</td>
                                                        <td>{signal.Index_Symbol || '-'}</td>
                                                        <td>{signal.GroupService || '-'}</td>
                                                        {/* <td>{signal.strategy || '-'}</td> */}
                                                        <td>{signal.broker || '-'}</td>
                                                        <td>{signal.Entry_type || '-'}</td>
                                                        <td>{signal.Exit_type || '-'}</td>
                                                        <td>{signal.EntryQty || '-'}</td>
                                                        <td>{signal.ExitQty || '-'}</td>
                                                        <td>{signal.Entry_Price !== null ? signal.Entry_Price : '-'}</td>
                                                        <td>{signal.Exit_Price !== null ? signal.Exit_Price : '-'}</td>
                                                        <td style={{ color: totalValue < 0 ? 'red' : 'green', fontWeight: 'bold' }}>
                                                            {total !== null ? total : '-'}
                                                        </td>
                                                        <td>{signal.order_status || '-'}</td>
                                                        <td>{signal.client?.full_name || '-'}</td>
                                                        <td>{signal.failure_reason || '-'}</td>
                                                    </tr>
                                                );
                                            })
                                        ) : (
                                            <tr>
                                                <td colSpan="10" style={{ textAlign: 'center' }}>No Client Trade Found</td>
                                            </tr>
                                        )}
                                    </tbody>
                                </Table>
                            </div>


                            {/* Pagination */}
                            <div className={`d-flex justify-content-end align-items-center ${isMobile ? 'gap-0' : 'gap-0'} custom-pagi-style`}>
                                <p className="mb-0 me-2">Rows per page</p>
                                <Input
                                    type="select"
                                    value={itemsPerPage}
                                    onChange={(e) => {
                                        setItemsPerPage(parseInt(e.target.value));
                                        setCurrentPage(1); // Reset to page 1 when changing items per page
                                    }}
                                    style={{ width: '80px' }}
                                    className="me-3"
                                >
                                    <option value="10">10</option>
                                    <option value="25">25</option>
                                    <option value="50">50</option>
                                </Input>

                                <Pagination>
                                    {/* Previous button */}
                                    <PaginationItem disabled={currentPage === 1}>
                                        <PaginationLink previous onClick={handlePrevious}>
                                            {isMobile ? 'Pre' : 'Previous'}
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

export default TradeView;
