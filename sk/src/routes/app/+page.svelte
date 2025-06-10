<script lang="ts">
  import Button from "$lib/components/ui/button/button.svelte";
  import { expenses } from "$lib/stores/data/expenses";
  import * as AlertDialog from "$lib/components/ui/alert-dialog/index.js";
  import { client } from "$lib/pocketbase";
  import { updateDataStores, UpdateFilterEnum } from "$lib/stores/data/load";
  import { toast } from "svelte-sonner";
  import { Lightbox } from "svelte-lightbox";
  import { getFileUrl } from "$lib/utils/file.utils";
  import { saveAs } from "file-saver";
  import Papa from "papaparse";
  import * as Drawer from "$lib/components/ui/drawer/index.js";
  import { writable } from "svelte/store";
  import * as Table from "$lib/components/ui/table";
  import { Input } from "$lib/components/ui/input";
  import {
    DateFormatter,
    getLocalTimeZone,
    parseDate,
    type DateValue
  } from "@internationalized/date";
  import { customers } from "$lib/stores/data/customers";
  import { expenseTypes } from "$lib/stores/data/expense_types";
  import * as Dialog from "$lib/components/ui/dialog";
  import { Label } from "$lib/components/ui/label";
  import { Checkbox } from "$lib/components/ui/checkbox";
  import {
    Camera,
    Search,
    ArrowUpDown,
    Calendar as CalendarIcon,
    ChevronDown,
    ChevronUp,
    Edit2,
    Trash2,
    Check,
    FileText,
    Download,
    Loader2
  } from "lucide-svelte";
  import { Card } from "$lib/components/ui/card";
  import * as DropdownMenu from "$lib/components/ui/dropdown-menu/index.js";
  import * as Popover from "$lib/components/ui/popover/index.js";
  import * as Command from "$lib/components/ui/command/index.js";
  import { cn } from "$lib/utils";
  import { tick } from "svelte";
  import { Calendar } from "$lib/components/ui/calendar/index.js";
  import { CaretSort } from "svelte-radix";
  // @ts-ignore
  import ExcelJS from "exceljs";
  import JSZip from "jszip";
  import type { ExpensesResponseWithExpand } from "$lib/pocketbase/generated-types";
  // @ts-ignore
  import { jsPDF } from "jspdf";
  import { getExpenseUnit, formatExpenseAmount } from "$lib/utils/expense.utils";

  interface Expense {
    collectionId: string;
    id: string;
    customer: string;
    date: string;
    type: string;
    amount: number;
    created: string;
    picture: string;
    company_credit_card: boolean;
    user: string;
    description: string;
    datetime: string;
    expense_type: string;
    customer_id: string;
    picture_filename: string;
  }

  type SortableField =
    | "date"
    | "amount"
    | "customer"
    | "type"
    | "description"
    | "company_credit_card"
    | "user";

  let tempExpenses: Expense[] = [];
  let searchQuery = "";
  let sortField: SortableField = "date";
  let sortDirection: "asc" | "desc" = "desc";

  // Get current date for filters and CSV export
  const currentDate = new Date();
  const currentMonth = currentDate.getMonth();
  const currentYear = currentDate.getFullYear();

  let selectedFilterMonth: string = currentMonth.toString();
  let selectedFilterYear: number = currentYear;
  let selectedMonth: string = (currentMonth + 1).toString().padStart(2, "0");
  let selectedYear: string = currentYear.toString();

  const drawerOpen = writable(false);
  let selectedRow: Expense | null = null;
  let editingExpense: Expense | null = null;
  let editDialogOpen = false;
  let deleteDialogOpen = false;
  let expenseToDelete: Expense | null = null;
  let newPicture: File | null = null;
  let editDateOpen = false;
  let editDateValue: DateValue | undefined = undefined;

  // For edit form
  let parsedCustomers: Array<{ value: string; label: string; frequency: number }> = [];
  let parsedExpenseTypes: Array<{ value: string; label: string; frequency: number }> = [];
  let editCustomerOpen = false;
  let editExpenseTypeOpen = false;

  let customerOpen = false;
  let customerValue = "";
  let expenseTypeOpen = false;
  let expenseTypeValue = "";

  $: editExpenseUnit = editingExpense ? getExpenseUnit(editingExpense.type) : "CHF";

  // For frequency tracking
  $: {
    // Count frequency of customers in expenses
    const customerFrequency = $expenses.reduce(
      (acc, expense) => {
        const customerId = expense.customer;
        acc[customerId] = (acc[customerId] || 0) + 1;
        return acc;
      },
      {} as Record<string, number>
    );

    // Count frequency of expense types per customer
    const customerTypeFrequency = $expenses.reduce(
      (acc, expense) => {
        const customerId = expense.customer;
        const typeId = expense.expense_type;
        if (!acc[customerId]) {
          acc[customerId] = {};
        }
        acc[customerId][typeId] = (acc[customerId][typeId] || 0) + 1;
        return acc;
      },
      {} as Record<string, Record<string, number>>
    );

    // Count frequency of customers per type
    const typeCustomerFrequency = $expenses.reduce(
      (acc, expense) => {
        const typeId = expense.expense_type;
        const customerId = expense.customer;
        if (!acc[typeId]) {
          acc[typeId] = {};
        }
        acc[typeId][customerId] = (acc[typeId][customerId] || 0) + 1;
        return acc;
      },
      {} as Record<string, Record<string, number>>
    );

    // Map and sort customers based on context
    parsedCustomers = $customers
      .map((customer) => ({
        value: customer.id,
        label: customer.name,
        frequency: customerFrequency[customer.id] || 0,
        // If a type is selected, use the frequency of this customer with that type
        contextFrequency: expenseTypeValue
          ? typeCustomerFrequency[expenseTypeValue]?.[customer.id] || 0
          : 0
      }))
      .sort((a, b) => {
        // If we have a type selected, sort by context frequency first
        if (expenseTypeValue) {
          const contextDiff = b.contextFrequency - a.contextFrequency;
          if (contextDiff !== 0) return contextDiff;
        }
        // Fall back to overall frequency
        return b.frequency - a.frequency;
      });

    // Map and sort expense types based on context
    parsedExpenseTypes = $expenseTypes
      .map((expenseType) => ({
        value: expenseType.id,
        label: expenseType.name,
        frequency: customerFrequency[expenseType.id] || 0,
        // If a customer is selected, use the frequency of this type with that customer
        contextFrequency: customerValue
          ? customerTypeFrequency[customerValue]?.[expenseType.id] || 0
          : 0
      }))
      .sort((a, b) => {
        // If we have a customer selected, sort by context frequency first
        if (customerValue) {
          const contextDiff = b.contextFrequency - a.contextFrequency;
          if (contextDiff !== 0) return contextDiff;
        }
        // Fall back to overall frequency
        return b.frequency - a.frequency;
      });
  }

  function closeCustomerCombobox(triggerId: string) {
    customerOpen = false;
    tick().then(() => {
      document.getElementById(triggerId)?.focus();
    });
  }

  function closeExpenseTypeCombobox(triggerId: string) {
    expenseTypeOpen = false;
    tick().then(() => {
      document.getElementById(triggerId)?.focus();
    });
  }

  const sortFields: SortableField[] = [
    "customer",
    "date",
    "type",
    "description",
    "amount",
    "company_credit_card"
  ];
  if (client.authStore.model?.admin) {
    sortFields.push("user");
  }

  function handleSort(field: SortableField) {
    if (sortField === field) {
      // If clicking the same field, toggle direction
      sortDirection = sortDirection === "asc" ? "desc" : "asc";
    } else {
      // If clicking a new field, set it as sort field and default to desc
      sortField = field;
      sortDirection = "desc";
    }
  }

  $: tempExpenses = $expenses.map((expense) => ({
    collectionId: expense.collectionId,
    id: expense.id,
    // @ts-expect-error - expense type is not null
    customer: expense.expand.customer.name,
    customer_id: expense.customer,
    date: new Date(expense.datetime).toLocaleDateString("de-CH", {
      year: "numeric",
      month: "short",
      day: "numeric"
    }),
    // @ts-expect-error - expense type is not null
    type: expense.expand.expense_type.name,
    expense_type: expense.expense_type,
    description: expense.description,
    amount: expense.amount,
    created: new Date(expense.created).toLocaleDateString("de-CH", {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "numeric",
      minute: "numeric"
    }),
    datetime: expense.datetime,
    picture: expense.picture ? getFileUrl(expense.collectionId, expense.id, expense.picture) : "",
    picture_filename: expense.picture || "",
    company_credit_card: expense.company_credit_card,
    // @ts-expect-error - expense type is not null
    user: expense.expand.user.name
  }));

  $: filteredByMonthExpenses = tempExpenses.filter((expense) => {
    if (selectedFilterMonth === "all") return true;
    const expenseDate = new Date(expense.datetime);
    return expenseDate.getMonth() === parseInt(selectedFilterMonth);
  });

  $: sortedAndFilteredExpenses = filteredByMonthExpenses
    .filter((expense) => {
      if (!searchQuery) return true;
      const query = searchQuery.toLowerCase();
      return (
        expense.customer.toLowerCase().includes(query) ||
        expense.type.toLowerCase().includes(query) ||
        expense.description?.toLowerCase().includes(query) ||
        expense.amount.toString().includes(query) ||
        expense.date.toLowerCase().includes(query) ||
        (expense.company_credit_card ? "company card" : "").includes(query) ||
        expense.user?.toLowerCase().includes(query)
      );
    })
    .sort((a, b) => {
      if (!sortField) return 0;

      const direction = sortDirection === "asc" ? 1 : -1;

      switch (sortField) {
        case "amount":
          return (a.amount - b.amount) * direction;
        case "company_credit_card":
          return (Number(a.company_credit_card) - Number(b.company_credit_card)) * direction;
        case "date":
          return (new Date(a.datetime).getTime() - new Date(b.datetime).getTime()) * direction;
        case "customer":
          return a.customer.localeCompare(b.customer) * direction;
        case "type":
          return a.type.localeCompare(b.type) * direction;
        case "description":
          return (a.description || "").localeCompare(b.description || "") * direction;
        case "user":
          return (a.user || "").localeCompare(b.user || "") * direction;
        default:
          return 0;
      }
    });

  function handleDeleteClick(expense: Expense) {
    expenseToDelete = expense;
    deleteDialogOpen = true;
  }

  async function confirmDelete() {
    if (!expenseToDelete) return;

    try {
      await client.collection("expenses").delete(expenseToDelete.id);
      await updateDataStores({
        filter: UpdateFilterEnum.ALL
      });
      toast.success("Expense deleted successfully!");
      deleteDialogOpen = false;
      expenseToDelete = null;
    } catch (error) {
      console.error(error);
      toast.error("Failed to delete expense!");
    }
  }

  function handleEditClick(expense: Expense) {
    editingExpense = { ...expense };
    editDateValue = parseDate(new Date(expense.datetime).toISOString().split("T")[0]);
    editDialogOpen = true;
  }

  function handleFileChange(event: Event) {
    const input = event.target as HTMLInputElement;
    if (input.files && input.files[0]) {
      const file = input.files[0];
      if (file.type === "application/pdf" || file.type.startsWith("image/")) {
        newPicture = file;
      } else {
        toast.error("Please upload a PDF or image file.");
        input.value = "";
      }
    }
  }

  async function handleEditSubmit() {
    if (!editingExpense || !editDateValue) return;

    const formData = new FormData();
    formData.append("datetime", editDateValue.toDate(getLocalTimeZone()).toISOString());
    formData.append("customer", editingExpense.customer_id);
    formData.append("expense_type", editingExpense.expense_type);
    formData.append("description", editingExpense.description);
    formData.append("amount", editingExpense.amount.toString());
    formData.append("company_credit_card", editingExpense.company_credit_card.toString());

    if (newPicture) {
      formData.append("picture", newPicture);
    }

    try {
      await client.collection("expenses").update(editingExpense.id, formData);
      await updateDataStores({
        filter: UpdateFilterEnum.ALL
      });
      toast.success("Expense updated successfully!");
      editDialogOpen = false;
      editingExpense = null;
      editDateValue = undefined;
      newPicture = null;
    } catch (error) {
      console.error(error);
      toast.error("Failed to update expense!");
    }
  }

  function downloadCSV(): void {
    const germanToEnglishMonths: { [key: string]: string } = {
      "Jan.": "Jan",
      "Feb.": "Feb",
      März: "Mar",
      "Apr.": "Apr",
      Mai: "May",
      Juni: "Jun",
      Juli: "Jul",
      "Aug.": "Aug",
      "Sept.": "Sep",
      "Okt.": "Oct",
      "Nov.": "Nov",
      "Dez.": "Dec"
    };

    const normalizedDates = tempExpenses.map((expense: { date: string }) => {
      let dateStr = expense.date;
      Object.keys(germanToEnglishMonths).forEach((germanMonth) => {
        dateStr = dateStr.replace(germanMonth, germanToEnglishMonths[germanMonth]);
      });
      return new Date(dateStr);
    });

    const filteredExpenses = tempExpenses.filter((expense: { date: string }, index: number) => {
      const date = normalizedDates[index];
      return (
        date.getMonth() + 1 === parseInt(selectedMonth) &&
        date.getFullYear() === parseInt(selectedYear)
      );
    });

    const csvData = filteredExpenses.map((expense) => ({
      ...expense,
      amount: formatExpenseAmount(expense.amount, expense.type)
    }));

    const csv = Papa.unparse(csvData);
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
    saveAs(blob, `expenses_${selectedYear}-${selectedMonth}.csv`);
  }

  function handleSubmit() {
    downloadCSV();
    drawerOpen.set(false);
  }

  let summaryDialogOpen = false;
  let summaryStartDate: DateValue | undefined = undefined;
  let summaryEndDate: DateValue | undefined = undefined;
  let summaryGenerating = false;
  let processingProgress = 0;
  let totalFiles = 0;
  let processedFiles = 0;
  let dateOpen = false;
  let startDateOpen = false;
  let endDateOpen = false;

  // Swiss German Calendar
  const df = new DateFormatter("de-CH", {
    dateStyle: "long"
  });

  function formatDateString(dateString: string): string {
    const date = new Date(dateString);
    return date.toLocaleDateString("de-CH");
  }

  interface ExcelRowData {
    pdf_index: number;
    id: string;
    date: string;
    customer: string;
    user: string;
    picture: string;
    type: string;
    description: string;
    amount: string;
    company_credit_card: string;
    receipt_status: string;
    file_type: string;
  }

  function createExcelWorkbook(data: ExcelRowData[]) {
    const workbook = new ExcelJS.Workbook();
    const worksheet = workbook.addWorksheet("Sheet1");

    // Add column headers
    worksheet.columns = [
      { header: "PDF Index", key: "pdf_index", width: 10 },
      { header: "ID", key: "id", width: 25 },
      { header: "Date", key: "date", width: 12 },
      { header: "Customer", key: "customer", width: 25 },
      { header: "User", key: "user", width: 15 },
      { header: "Picture", key: "picture", width: 30 },
      { header: "Type", key: "type", width: 20 },
      { header: "Description", key: "description", width: 30 },
      { header: "Amount", key: "amount", width: 12 },
      { header: "Company Card", key: "company_credit_card", width: 15 },
      { header: "Receipt Status", key: "receipt_status", width: 15 },
      { header: "File Type", key: "file_type", width: 10 }
    ];

    // Format header row
    worksheet.getRow(1).font = { bold: true, color: { argb: "FFFFFF" } };
    worksheet.getRow(1).fill = { type: "pattern", pattern: "solid", fgColor: { argb: "2C3E50" } };
    worksheet.getRow(1).alignment = { horizontal: "center", vertical: "middle" };

    // Add data rows
    data.forEach((row, index) => {
      worksheet.addRow(row);

      // Add alternating row colors
      if (index % 2 === 1) {
        worksheet.getRow(index + 2).fill = {
          type: "pattern",
          pattern: "solid",
          fgColor: { argb: "F5F5F5" }
        };
      }
    });

    // Add conditional formatting for receipt status
    worksheet.addConditionalFormatting({
      ref: `K2:K${data.length + 1}`,
      rules: [
        {
          type: "containsText",
          operator: "containsText",
          text: "Available",
          style: { fill: { type: "pattern", pattern: "solid", bgColor: { argb: "C6EFCE" } } }
        },
        {
          type: "containsText",
          operator: "containsText",
          text: "Missing",
          style: { fill: { type: "pattern", pattern: "solid", bgColor: { argb: "FFC7CE" } } }
        },
        {
          type: "containsText",
          operator: "containsText",
          text: "Failed",
          style: { fill: { type: "pattern", pattern: "solid", bgColor: { argb: "FFEB9C" } } }
        }
      ]
    });

    return workbook;
  }

  async function fetchFileFromUrl(url: string): Promise<ArrayBuffer | null> {
    try {
      // Fetch the file using the browser's fetch API
      const response = await fetch(url);

      if (!response.ok) {
        throw new Error(`Failed to fetch: ${response.status} ${response.statusText}`);
      }

      // Get the array buffer from the response
      const arrayBuffer = await response.arrayBuffer();
      return arrayBuffer;
    } catch (error) {
      console.error("Error fetching file:", error);
      return null;
    }
  }

  async function convertImageToPdf(imageUrl: string): Promise<ArrayBuffer | null> {
    try {
      // Create a new image element
      const img = new Image();

      // Wait for the image to load
      await new Promise((resolve, reject) => {
        img.onload = resolve;
        img.onerror = reject;
        img.src = imageUrl;
      });

      // Calculate dimensions (maintain aspect ratio)
      const imgWidth = img.width;
      const imgHeight = img.height;
      const pageWidth = 210; // A4 width in mm

      // Calculate height based on A4 width and original aspect ratio
      const pageHeight = (pageWidth * imgHeight) / imgWidth;

      // Create PDF with calculated dimensions
      const pdf = new jsPDF({
        orientation: pageHeight > pageWidth ? "portrait" : "landscape",
        unit: "mm",
        format: [pageWidth, pageHeight]
      });

      // Add image to PDF (convert dimensions to mm)
      pdf.addImage(img, "JPEG", 0, 0, pageWidth, pageHeight);

      // Convert PDF to ArrayBuffer
      const pdfArrayBuffer = pdf.output("arraybuffer");
      return pdfArrayBuffer;
    } catch (error) {
      console.error("Error converting image to PDF:", error);
      return null;
    }
  }

  function isFileTypePdf(url: string | null | undefined): boolean {
    if (!url) return false;
    return url.toLowerCase().endsWith(".pdf");
  }

  async function generateSummary() {
    if (!summaryStartDate || !summaryEndDate) {
      toast.error("Please select a date range");
      return;
    }

    summaryGenerating = true;
    processingProgress = 0;
    try {
      const startDate = summaryStartDate.toDate(getLocalTimeZone());
      const endDate = summaryEndDate.toDate(getLocalTimeZone());

      // Set start date to beginning of day (00:00:00) and end date to end of day (23:59:59)
      startDate.setHours(0, 0, 0, 0);
      endDate.setHours(23, 59, 59, 999);

      // Format start and end dates for the PocketBase filter
      // Ensure consistent UTC format for querying
      const startISO = startDate.toISOString();
      const endISO = endDate.toISOString();

      console.log("Date range:", startISO, "to", endISO);

      const periodStr = `${startDate.getFullYear()}-${(startDate.getMonth() + 1).toString().padStart(2, "0")}`;

      // Get all expenses first
      const expensesResult = await client
        .collection("expenses")
        .getList<ExpensesResponseWithExpand>(1, 1000, {
          sort: "datetime",
          expand: "customer,expense_type,user"
        });

      // Filter locally to ensure all expenses within range are included
      const filteredExpenses = expensesResult.items.filter((expense) => {
        const expenseDate = new Date(expense.datetime);
        return expenseDate >= startDate && expenseDate <= endDate;
      });

      console.log(
        `Found ${filteredExpenses.length} expenses in date range from ${expensesResult.items.length} total`
      );

      // Prepare data for Excel - include ALL expenses regardless of receipt status
      const excelData = filteredExpenses.map((expense, index) => {
        const receiptStatus = expense.picture ? "Available" : "Missing";
        const fileUrl = expense.picture
          ? getFileUrl(expense.collectionId, expense.id, expense.picture)
          : "";
        const isPdf = isFileTypePdf(expense.picture);

        const expenseTypeName = expense.expand?.expense_type?.name || "";
        return {
          pdf_index: index,
          id: expense.id,
          date: formatDateString(expense.datetime),
          customer: expense.expand?.customer?.name || "",
          user: expense.expand?.user?.name || "",
          picture: fileUrl,
          picture_filename: expense.picture || "",
          type: expenseTypeName,
          description: expense.description || "",
          amount: formatExpenseAmount(expense.amount, expenseTypeName),
          company_credit_card: expense.company_credit_card ? "Yes" : "No",
          receipt_status: receiptStatus,
          file_type: expense.picture ? (isPdf ? "pdf" : "image") : ""
        };
      });

      // Create Excel workbook with ALL expenses
      const workbook = createExcelWorkbook(excelData);

      // Create ZIP file with Excel and PDFs
      const zip = new JSZip();

      // Add Excel file to ZIP
      const excelBuffer = await workbook.xlsx.writeBuffer();
      zip.file(`processed_expenses_${periodStr}.xlsx`, excelBuffer);

      // Create a folder for receipts
      const receiptsFolder = zip.folder("receipts");

      // Count total files to process for progress tracking - only process expenses WITH receipts
      const filesToProcess = excelData.filter((row) => row.receipt_status === "Available");
      totalFiles = filesToProcess.length;
      processedFiles = 0;

      // Add PDFs to ZIP - only for expenses WITH receipts
      if (receiptsFolder) {
        const filePromises = filesToProcess.map(async (row) => {
          try {
            const isPdf = isFileTypePdf(row.picture_filename);
            const fileName = `${String(row.pdf_index).padStart(4, "0")}_${row.date}_${row.id}.pdf`;

            // For PDFs, add them directly
            if (isPdf) {
              const fileData = await fetchFileFromUrl(row.picture);
              if (fileData) {
                receiptsFolder.file(fileName, fileData);
                processedFiles++;
                processingProgress = Math.round((processedFiles / totalFiles) * 100);
                return true;
              }
            }
            // For images, convert to PDF first
            else {
              const pdfData = await convertImageToPdf(row.picture);
              if (pdfData) {
                receiptsFolder.file(fileName, pdfData);
                processedFiles++;
                processingProgress = Math.round((processedFiles / totalFiles) * 100);
                return true;
              }
            }
            return false;
          } catch (error) {
            console.error(`Failed to process file for expense ${row.id}:`, error);
            processedFiles++;
            processingProgress = Math.round((processedFiles / totalFiles) * 100);
            return false;
          }
        });

        await Promise.all(filePromises);
      }

      // Generate the ZIP file
      const zipContent = await zip.generateAsync({ type: "blob" });

      // Trigger download
      saveAs(zipContent, `processed_expenses_${periodStr}.zip`);

      toast.success("Summary generated successfully!");
      summaryDialogOpen = false;
    } catch (error) {
      console.error("Error generating summary:", error);
      toast.error("Failed to generate summary");
    } finally {
      summaryGenerating = false;
    }
  }
</script>

<div class="container mx-auto py-6 px-4">
  <div class="flex flex-col sm:flex-row items-center justify-between gap-4 mb-6">
    <div class="flex gap-2 w-full sm:w-auto">
      <div class="relative w-full sm:w-auto sm:min-w-[300px]">
        <Search class="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
        <Input type="text" placeholder="Search expenses..." class="pl-8" bind:value={searchQuery} />
      </div>
      <DropdownMenu.Root>
        <DropdownMenu.Trigger asChild let:builder>
          <Button variant="outline" builders={[builder]} class="w-[180px]">
            {#if selectedFilterMonth === "all"}
              All Expenses
            {:else}
              {new Date(selectedFilterYear, parseInt(selectedFilterMonth), 1).toLocaleDateString(
                "de-CH",
                { month: "long", year: "numeric" }
              )}
            {/if}
            <ChevronDown class="ml-2 h-4 w-4" />
          </Button>
        </DropdownMenu.Trigger>
        <DropdownMenu.Content align="end">
          <DropdownMenu.Label>Filter by Month</DropdownMenu.Label>
          <DropdownMenu.Separator />
          <DropdownMenu.RadioGroup bind:value={selectedFilterMonth}>
            <DropdownMenu.RadioItem value="all">All Expenses</DropdownMenu.RadioItem>
            <DropdownMenu.RadioItem value={currentMonth.toString()}>
              {new Date(currentYear, currentMonth).toLocaleDateString("de-CH", { month: "long" })}
            </DropdownMenu.RadioItem>
            <DropdownMenu.RadioItem
              value={(currentMonth - 1 >= 0 ? currentMonth - 1 : 11).toString()}
            >
              {new Date(
                currentYear,
                currentMonth - 1 >= 0 ? currentMonth - 1 : 11
              ).toLocaleDateString("de-CH", { month: "long" })}
            </DropdownMenu.RadioItem>
          </DropdownMenu.RadioGroup>
        </DropdownMenu.Content>
      </DropdownMenu.Root>
    </div>
    {#if client.authStore.model && client.authStore.model.admin}
      <div class="flex gap-2">
        <Button variant="outline" on:click={() => drawerOpen.set(true)}>Download CSV</Button>
        <Button variant="outline" on:click={() => (summaryDialogOpen = true)}>
          <FileText class="h-4 w-4 mr-2" />
          Generate PDF Summary
        </Button>
      </div>
    {/if}
  </div>

  <!-- Desktop Table View -->
  <div class="hidden md:block rounded-md border overflow-x-auto">
    <Table.Root>
      <Table.Header>
        <Table.Row>
          {#each sortFields as field}
            <Table.Head class="min-w-[150px] cursor-pointer select-none hover:bg-muted/50">
              <button
                class="flex items-center gap-1 w-full text-left"
                on:click|stopPropagation={() => handleSort(field)}
              >
                <span class="capitalize">{field.replace(/_/g, " ")}</span>
                {#if sortField === field}
                  <span class="text-primary">
                    {#if sortDirection === "asc"}
                      <ChevronUp class="h-4 w-4" />
                    {:else}
                      <ChevronDown class="h-4 w-4" />
                    {/if}
                  </span>
                {:else}
                  <ArrowUpDown class="h-4 w-4 opacity-0 group-hover:opacity-100" />
                {/if}
              </button>
            </Table.Head>
          {/each}
          <Table.Head class="w-[150px]">Actions</Table.Head>
        </Table.Row>
      </Table.Header>
      <Table.Body>
        {#each sortedAndFilteredExpenses as expense}
          <Table.Row>
            <Table.Cell>{expense.customer}</Table.Cell>
            <Table.Cell>{expense.date}</Table.Cell>
            <Table.Cell>{expense.type}</Table.Cell>
            <Table.Cell>{expense.description}</Table.Cell>
            <Table.Cell class="text-right font-medium"
              >{formatExpenseAmount(expense.amount, expense.type)}</Table.Cell
            >
            <Table.Cell>
              {#if expense.company_credit_card}
                <span
                  class="bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-100 text-xs px-2 py-0.5 rounded"
                  >Company Card</span
                >
              {:else}
                <span
                  class="bg-orange-100 dark:bg-orange-900 text-orange-800 dark:text-orange-100 text-xs px-2 py-0.5 rounded"
                  >Self Paid</span
                >
              {/if}
            </Table.Cell>
            {#if client.authStore.model?.admin}
              <Table.Cell>{expense.user}</Table.Cell>
            {/if}
            <Table.Cell>
              <div class="flex justify-end gap-2">
                {#if expense.picture}
                  <div class="flex items-center space-x-2">
                    {#if isFileTypePdf(expense.picture_filename)}
                      <a
                        href={expense.picture}
                        target="_blank"
                        rel="noopener noreferrer"
                        class="text-blue-500 hover:text-blue-700"
                      >
                        View PDF
                      </a>
                    {:else}
                      <Lightbox>
                        <div slot="thumbnail">
                          <img
                            src={expense.picture}
                            alt="Expense receipt"
                            class="w-16 h-16 object-cover rounded cursor-pointer"
                          />
                        </div>
                        <div>
                          <img src={expense.picture} alt="Expense receipt" class="max-h-[80vh]" />
                        </div>
                      </Lightbox>
                    {/if}
                  </div>
                {/if}
                <Button variant="ghost" size="icon" on:click={() => handleEditClick(expense)}>
                  <Edit2 class="h-4 w-4" />
                </Button>
                <Button variant="ghost" size="icon" on:click={() => handleDeleteClick(expense)}>
                  <Trash2 class="h-4 w-4" />
                </Button>
              </div>
            </Table.Cell>
          </Table.Row>
        {/each}
      </Table.Body>
    </Table.Root>
  </div>

  <!-- Mobile Card View -->
  <div class="block md:hidden space-y-4">
    {#each sortedAndFilteredExpenses as expense}
      <Card class="p-4">
        <div class="space-y-2 mb-2">
          <div class="flex items-center justify-between">
            <span class="font-medium">{expense.customer}</span>
            <div class="text-right font-medium">
              {formatExpenseAmount(expense.amount, expense.type)}
            </div>
          </div>
          <div>
            {#if expense.company_credit_card}
              <span
                class="bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-100 text-xs px-2 py-0.5 rounded"
                >Company Card</span
              >
            {:else}
              <span
                class="bg-orange-100 dark:bg-orange-900 text-orange-800 dark:text-orange-100 text-xs px-2 py-0.5 rounded"
                >Self Paid</span
              >
            {/if}
          </div>
        </div>

        {#if expense.picture}
          <div class="mb-3 w-full">
            <div class="flex items-center space-x-2">
              {#if isFileTypePdf(expense.picture_filename)}
                <a
                  href={expense.picture}
                  target="_blank"
                  rel="noopener noreferrer"
                  class="text-blue-500 hover:text-blue-700"
                >
                  View PDF
                </a>
              {:else}
                <Lightbox>
                  <div slot="thumbnail">
                    <img
                      src={expense.picture}
                      alt="Expense receipt"
                      class="w-full h-20 object-cover rounded-lg"
                    />
                  </div>
                  <div>
                    <img src={expense.picture} alt="Expense receipt" class="max-h-[80vh]" />
                  </div>
                </Lightbox>
              {/if}
            </div>
          </div>
        {/if}

        <div class="grid grid-cols-2 gap-2 text-sm mb-3">
          <div class="flex items-center gap-1 text-muted-foreground">
            <CalendarIcon class="h-4 w-4" />
            {expense.date}
          </div>
          <div class="text-right text-muted-foreground">
            {expense.type}
          </div>
        </div>

        {#if expense.description}
          <p class="text-sm text-muted-foreground mb-3">
            {expense.description}
          </p>
        {/if}

        <div class="flex justify-end gap-2">
          <Button variant="ghost" size="icon" on:click={() => handleEditClick(expense)}>
            <Edit2 class="h-4 w-4" />
          </Button>
          <Button variant="ghost" size="icon" on:click={() => handleDeleteClick(expense)}>
            <Trash2 class="h-4 w-4" />
          </Button>
        </div>
      </Card>
    {/each}
  </div>
</div>

<!-- Dialogs and Drawers -->
<Dialog.Root bind:open={editDialogOpen}>
  <Dialog.Content>
    <Dialog.Header>
      <Dialog.Title>Edit Expense</Dialog.Title>
      <Dialog.Description>Make changes to the expense entry</Dialog.Description>
    </Dialog.Header>

    {#if editingExpense}
      <form class="grid gap-4" on:submit|preventDefault={handleEditSubmit}>
        <Popover.Root bind:open={editDateOpen} let:ids>
          <Popover.Trigger asChild let:builder>
            <Button
              variant="outline"
              class={cn("w-full justify-start text-left font-normal")}
              builders={[builder]}
            >
              <CalendarIcon class="mr-2 h-4 w-4" />
              {editDateValue
                ? editDateValue
                    .toDate(getLocalTimeZone())
                    .toLocaleDateString("de-CH", { dateStyle: "long" })
                : "Select date"}
            </Button>
          </Popover.Trigger>
          <Popover.Content class="w-auto p-0" align="center">
            <Calendar bind:value={editDateValue} />
          </Popover.Content>
        </Popover.Root>

        <Popover.Root bind:open={editCustomerOpen} let:ids>
          <Popover.Trigger asChild let:builder>
            <Button
              builders={[builder]}
              variant="outline"
              role="combobox"
              aria-expanded={editCustomerOpen}
              class="w-full justify-between"
            >
              {editingExpense.customer || "Select customer"}
              <CaretSort class="ml-2 h-4 w-4 shrink-0 opacity-50" />
            </Button>
          </Popover.Trigger>
          <Popover.Content class="w-[200px] p-0">
            <Command.Root>
              <Command.Input placeholder="Search customers..." class="h-9" />
              <Command.Empty>No customer found.</Command.Empty>
              <Command.Group>
                {#each parsedCustomers as customer}
                  <Command.Item
                    value={customer.label}
                    onSelect={() => {
                      if (editingExpense) {
                        editingExpense.customer_id = customer.value;
                        editingExpense.customer = customer.label;
                        closeCustomerCombobox(ids.trigger);
                      }
                    }}
                  >
                    <Check
                      class={cn(
                        "mr-2 h-4 w-4",
                        editingExpense.customer_id !== customer.value && "text-transparent"
                      )}
                    />
                    <span class="flex-1">{customer.label}</span>
                    {#if customer.frequency > 0}
                      <span class="text-xs text-muted-foreground ml-2">{customer.frequency}x</span>
                    {/if}
                  </Command.Item>
                {/each}
              </Command.Group>
            </Command.Root>
          </Popover.Content>
        </Popover.Root>

        <Popover.Root bind:open={editExpenseTypeOpen} let:ids>
          <Popover.Trigger asChild let:builder>
            <Button
              builders={[builder]}
              variant="outline"
              role="combobox"
              aria-expanded={editExpenseTypeOpen}
              class="w-full justify-between"
            >
              {editingExpense.type || "Select type"}
              <CaretSort class="ml-2 h-4 w-4 shrink-0 opacity-50" />
            </Button>
          </Popover.Trigger>
          <Popover.Content class="w-[200px] p-0">
            <Command.Root>
              <Command.Input placeholder="Search expense type..." class="h-9" />
              <Command.Empty>No expense type found.</Command.Empty>
              <Command.Group>
                {#each parsedExpenseTypes as expenseType}
                  <Command.Item
                    value={expenseType.label}
                    onSelect={() => {
                      if (editingExpense) {
                        editingExpense.expense_type = expenseType.value;
                        editingExpense.type = expenseType.label;
                        editExpenseUnit = getExpenseUnit(expenseType.label);
                        closeExpenseTypeCombobox(ids.trigger);
                      }
                    }}
                  >
                    <Check
                      class={cn(
                        "mr-2 h-4 w-4",
                        editingExpense.expense_type !== expenseType.value && "text-transparent"
                      )}
                    />
                    <span class="flex-1">{expenseType.label}</span>
                    {#if expenseType.frequency > 0}
                      <span class="text-xs text-muted-foreground ml-2"
                        >{expenseType.frequency}x</span
                      >
                    {/if}
                  </Command.Item>
                {/each}
              </Command.Group>
            </Command.Root>
          </Popover.Content>
        </Popover.Root>

        <div class="grid gap-2">
          <Label for="edit-description">Description</Label>
          <Input id="edit-description" bind:value={editingExpense.description} />
        </div>
        <div class="grid gap-2">
          <Label for="edit-amount">Amount ({editExpenseUnit})</Label>
          <Input id="edit-amount" type="number" step="0.01" bind:value={editingExpense.amount} />
        </div>
        <div class="grid gap-2">
          <Label for="edit-picture">Receipt Picture</Label>
          {#if editingExpense.picture && !newPicture}
            <div class="mb-2">
              <img src={editingExpense.picture} alt="Current receipt" class="max-h-32 rounded-lg" />
            </div>
          {/if}
          {#if newPicture}
            <div class="mb-2">
              <img
                src={URL.createObjectURL(newPicture)}
                alt="New receipt"
                class="max-h-32 rounded-lg"
              />
            </div>
          {/if}
          <div class="file-input-wrapper">
            <input
              id="edit-picture"
              type="file"
              class="file-input"
              accept="image/*,application/pdf"
              on:change={handleFileChange}
            />
            <label
              for="edit-picture"
              class="inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 border border-input bg-background hover:bg-accent hover:text-accent-foreground h-10 px-4 py-2 w-full"
            >
              <Camera class="h-4 w-4 mr-2" />
              Upload New Picture
            </label>
          </div>
        </div>
        <div class="flex items-center space-x-2">
          <Checkbox id="edit-company-card" bind:checked={editingExpense.company_credit_card} />
          <Label for="edit-company-card">Company credit card used</Label>
        </div>
        <div class="flex justify-end gap-2">
          <Dialog.Close asChild let:builder>
            <Button variant="outline" builders={[builder]}>Cancel</Button>
          </Dialog.Close>
          <Button type="submit">Save changes</Button>
        </div>
      </form>
    {/if}
  </Dialog.Content>
</Dialog.Root>

<AlertDialog.Root bind:open={deleteDialogOpen}>
  <AlertDialog.Content>
    <AlertDialog.Header>
      <AlertDialog.Title>Are you sure?</AlertDialog.Title>
      <AlertDialog.Description>
        This action cannot be undone. This will permanently delete the expense
        {#if expenseToDelete}
          for {formatExpenseAmount(expenseToDelete.amount, expenseToDelete.type)} from {expenseToDelete.customer}.
        {/if}
      </AlertDialog.Description>
    </AlertDialog.Header>
    <AlertDialog.Footer>
      <AlertDialog.Cancel>Cancel</AlertDialog.Cancel>
      <AlertDialog.Action on:click={confirmDelete}>Delete</AlertDialog.Action>
    </AlertDialog.Footer>
  </AlertDialog.Content>
</AlertDialog.Root>

{#if client.authStore.model && client.authStore.model.admin}
  <Drawer.Root open={$drawerOpen}>
    <Drawer.Content>
      <div class="mx-auto w-full max-w-sm">
        <Drawer.Header>
          <Drawer.Title>Select Month and Year</Drawer.Title>
          <Drawer.Description>Select the month and year for the CSV export.</Drawer.Description>
        </Drawer.Header>
        <div class="p-4 pb-0">
          <div class="grid gap-4">
            <div class="grid gap-2">
              <Label for="month">Month</Label>
              <Input
                id="month"
                type="number"
                bind:value={selectedMonth}
                min="1"
                max="12"
                placeholder="MM"
              />
            </div>
            <div class="grid gap-2">
              <Label for="year">Year</Label>
              <Input
                id="year"
                type="number"
                bind:value={selectedYear}
                min="2000"
                max="2100"
                placeholder="YYYY"
              />
            </div>
          </div>
        </div>
        <Drawer.Footer>
          <Button on:click={handleSubmit}>Download</Button>
          <Drawer.Close asChild let:builder>
            <Button builders={[builder]} variant="outline">Cancel</Button>
          </Drawer.Close>
        </Drawer.Footer>
      </div>
    </Drawer.Content>
  </Drawer.Root>
{/if}

<Dialog.Root bind:open={summaryDialogOpen}>
  <Dialog.Content>
    <Dialog.Header>
      <Dialog.Title>Generate Expense Summary</Dialog.Title>
      <Dialog.Description>
        Select a date range to generate a ZIP file containing an Excel summary and PDF files for all
        expenses with receipts.
      </Dialog.Description>
    </Dialog.Header>
    <div class="grid gap-4 py-4">
      <div class="grid gap-2">
        <Label for="start-date">Start Date</Label>
        <Popover.Root bind:open={startDateOpen}>
          <Popover.Trigger asChild let:builder>
            <Button
              builders={[builder]}
              variant="outline"
              class={cn(
                "w-full justify-start text-left font-normal",
                !summaryStartDate && "text-muted-foreground"
              )}
            >
              <CalendarIcon class="mr-2 h-4 w-4" />
              {#if summaryStartDate}
                {df.format(summaryStartDate.toDate(getLocalTimeZone()))}
              {:else}
                <span>Pick a date</span>
              {/if}
            </Button>
          </Popover.Trigger>
          <Popover.Content class="w-auto p-0" align="start">
            <Calendar bind:value={summaryStartDate} initialFocus />
          </Popover.Content>
        </Popover.Root>
      </div>
      <div class="grid gap-2">
        <Label for="end-date">End Date</Label>
        <Popover.Root bind:open={endDateOpen}>
          <Popover.Trigger asChild let:builder>
            <Button
              builders={[builder]}
              variant="outline"
              class={cn(
                "w-full justify-start text-left font-normal",
                !summaryEndDate && "text-muted-foreground"
              )}
            >
              <CalendarIcon class="mr-2 h-4 w-4" />
              {#if summaryEndDate}
                {df.format(summaryEndDate.toDate(getLocalTimeZone()))}
              {:else}
                <span>Pick a date</span>
              {/if}
            </Button>
          </Popover.Trigger>
          <Popover.Content class="w-auto p-0" align="start">
            <Calendar bind:value={summaryEndDate} initialFocus />
          </Popover.Content>
        </Popover.Root>
      </div>

      {#if summaryGenerating}
        <div class="mt-2">
          <div class="mb-2 flex justify-between text-sm text-muted-foreground">
            <span>Processing {processedFiles} of {totalFiles} files</span>
            <span>{processingProgress}%</span>
          </div>
          <div class="h-2 w-full overflow-hidden rounded-full bg-muted">
            <div
              class="h-full bg-primary transition-all"
              style="width: {processingProgress}%"
            ></div>
          </div>
        </div>
      {/if}
    </div>
    <Dialog.Footer>
      <Button
        variant="outline"
        on:click={() => (summaryDialogOpen = false)}
        disabled={summaryGenerating}
      >
        Cancel
      </Button>
      <Button on:click={generateSummary} disabled={summaryGenerating}>
        {#if summaryGenerating}
          <Loader2 class="h-4 w-4 mr-2 animate-spin" />
          Generating...
        {:else}
          <Download class="h-4 w-4 mr-2" />
          Generate ZIP Package
        {/if}
      </Button>
    </Dialog.Footer>
  </Dialog.Content>
</Dialog.Root>

<style>
  .file-input-wrapper {
    position: relative;
    display: inline-block;
    width: 100%;
  }
  .file-input {
    display: none; /* Hide the actual file input */
  }
  .file-input-button {
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 10px;
    background-color: var(--background);
    border: 1px solid var(--border);
    border-radius: 4px;
    cursor: pointer;
    width: 100%;
    color: var(--foreground);
  }
  .file-input-button:hover {
    background-color: var(--muted);
  }
</style>
