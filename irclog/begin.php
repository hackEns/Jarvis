<!DOCTYPE html>
<?php
date_default_timezone_set('Europe/Paris');
$min_time = empty($_GET['from']) ? strtotime("midnight", time()) : intval($_GET['from']);
$max_time = empty($_GET['to']) ? strtotime("tomorrow", $min_time) - 1 : intval($_GET['to']);
$today = $min_time;
$one_day = 86400;

$show_all = false;
if (isset($_GET['all'])) {
    $min_time = 0;
    $max_time = 9999999999999999999999;
    $show_all= true;
}
?>
<html>
    <head>
        <title>Log of #hackens IRC channel</title>
        <meta charset="utf-8"/>
        <link rel="stylesheet" href="style.css" />
    </head>
    <body>
        <header>
            <h1>Log of #hackens IRC channel</h1>
            <?php if (!$show_all) { ?>
            <h2>Day <?=date('Y-m-d', $today)?></h2>
            <p>
                <a href="?from=<?=$today-$one_day?>&to=<?=$today?>">Previous day</a> <a href="?from=<?=$today+$one_day?>&to=<?=$today+2*$one_day?>">Next day</a>
            </p>
            <?php } ?>
        </header>
        <table>
            <tbody>

