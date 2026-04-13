package com.jureka.historicalmarkers.data

/**
 * DataSeeder — provides the initial list of real US historical markers.
 *
 * Each entry uses a stable [markerId] string (state + sequential number) so re-seeding
 * on every app launch is idempotent — Room's IGNORE conflict strategy skips duplicates.
 *
 * Markers span a variety of states and topics to demonstrate the app's breadth.
 * GPS coordinates are approximate centroid positions for the marker location.
 *
 * To add more markers: append new [Marker] objects to the list returned by [getDefaultMarkers].
 * Full national datasets are available from hmdb.org (Historical Marker Database).
 */
object DataSeeder {

    /**
     * Return a curated starter set of 30 real US historical markers.
     *
     * @return List of [Marker] objects ready for [MarkerRepository.seedMarkers].
     *
     * Example:
     *   DataSeeder.getDefaultMarkers().size  // → 30
     */
    fun getDefaultMarkers(): List<Marker> = listOf(

        // ─── Virginia ────────────────────────────────────────────────────────────
        Marker(
            markerId = "VA-0001", title = "Battle of Cedar Creek",
            description = "On October 19, 1864, Confederate forces under General Jubal Early " +
                "surprised the Union Army of the Shenandoah here at dawn. General Philip Sheridan's " +
                "famous ride from Winchester rallied his troops, who turned a near-defeat into a " +
                "decisive Union victory, effectively ending Confederate resistance in the Shenandoah Valley.",
            city = "Middletown", state = "VA", latitude = 39.0279, longitude = -78.2839
        ),
        Marker(
            markerId = "VA-0002", title = "Appomattox Court House",
            description = "On April 9, 1865, General Robert E. Lee surrendered the Army of Northern " +
                "Virginia to General Ulysses S. Grant in the parlor of Wilmer McLean's house here, " +
                "effectively ending the Civil War.",
            city = "Appomattox", state = "VA", latitude = 37.3640, longitude = -78.7981
        ),

        // ─── Pennsylvania ────────────────────────────────────────────────────────
        Marker(
            markerId = "PA-0001", title = "Declaration of Independence",
            description = "The Declaration of Independence was debated and adopted by the Second " +
                "Continental Congress in Independence Hall, just steps from this marker, on " +
                "July 4, 1776. The document proclaimed the thirteen colonies free and independent states.",
            city = "Philadelphia", state = "PA", latitude = 39.9484, longitude = -75.1503
        ),
        Marker(
            markerId = "PA-0002", title = "Battle of Gettysburg",
            description = "From July 1–3, 1863, this was the site of the largest battle ever " +
                "fought in North America. Union forces repelled a Confederate invasion of the North, " +
                "marking a turning point in the Civil War. President Lincoln delivered the Gettysburg " +
                "Address here on November 19, 1863.",
            city = "Gettysburg", state = "PA", latitude = 39.8112, longitude = -77.2314
        ),

        // ─── Massachusetts ───────────────────────────────────────────────────────
        Marker(
            markerId = "MA-0001", title = "Plymouth Rock",
            description = "Tradition holds that Plymouth Rock marks the spot where the Pilgrims " +
                "of the Mayflower first set foot on land in December 1620. The colony they founded " +
                "became one of the earliest permanent European settlements in New England.",
            city = "Plymouth", state = "MA", latitude = 41.9584, longitude = -70.6673
        ),
        Marker(
            markerId = "MA-0002", title = "Paul Revere's Ride",
            description = "On the night of April 18–19, 1775, Paul Revere rode from Boston to " +
                "Lexington to warn patriot leaders Samuel Adams and John Hancock that British " +
                "regulars were marching to seize colonial arms stores at Concord.",
            city = "Boston", state = "MA", latitude = 42.3668, longitude = -71.0560
        ),
        Marker(
            markerId = "MA-0003", title = "Battle of Lexington",
            description = "The 'shot heard round the world' was fired on Lexington Green on " +
                "April 19, 1775, opening the American Revolutionary War when 77 Minutemen " +
                "faced 700 British regulars.",
            city = "Lexington", state = "MA", latitude = 42.4494, longitude = -71.2317
        ),

        // ─── New York ─────────────────────────────────────────────────────────────
        Marker(
            markerId = "NY-0001", title = "Statue of Liberty Dedication",
            description = "France gifted the Statue of Liberty to the United States, and it was " +
                "dedicated on October 28, 1886 by President Grover Cleveland. Designed by Frédéric " +
                "Auguste Bartholdi, it became a universal symbol of freedom and democracy.",
            city = "New York", state = "NY", latitude = 40.6892, longitude = -74.0445
        ),
        Marker(
            markerId = "NY-0002", title = "Erie Canal Groundbreaking",
            description = "Ground was broken for the Erie Canal on July 4, 1817 near here. " +
                "When completed in 1825, the 363-mile waterway connected the Hudson River to " +
                "Lake Erie, opening the American interior to trade and migration.",
            city = "Rome", state = "NY", latitude = 43.2128, longitude = -75.4557
        ),

        // ─── Washington D.C. ─────────────────────────────────────────────────────
        Marker(
            markerId = "DC-0001", title = "Lincoln Memorial",
            description = "Dedicated in 1922, the Lincoln Memorial honors the 16th President of " +
                "the United States. Dr. Martin Luther King Jr. delivered his 'I Have a Dream' " +
                "speech from its steps on August 28, 1963 to more than 250,000 civil rights marchers.",
            city = "Washington", state = "DC", latitude = 38.8893, longitude = -77.0502
        ),
        Marker(
            markerId = "DC-0002", title = "Ford's Theatre",
            description = "President Abraham Lincoln was shot here by John Wilkes Booth on the " +
                "evening of April 14, 1865, while attending a performance of 'Our American Cousin.' " +
                "Lincoln died the following morning, becoming the first US president to be assassinated.",
            city = "Washington", state = "DC", latitude = 38.8965, longitude = -77.0257
        ),

        // ─── Illinois ────────────────────────────────────────────────────────────
        Marker(
            markerId = "IL-0001", title = "Great Chicago Fire Origin",
            description = "The Great Chicago Fire began near DeKoven Street on the night of " +
                "October 8, 1871. The fire burned for two days, destroying more than 17,000 " +
                "buildings and leaving roughly 100,000 residents homeless.",
            city = "Chicago", state = "IL", latitude = 41.8613, longitude = -87.6450
        ),
        Marker(
            markerId = "IL-0002", title = "Lincoln–Douglas Debate, Freeport",
            description = "On August 27, 1858, Abraham Lincoln and Stephen A. Douglas held " +
                "their second of seven famous debates here. Lincoln's direct questioning forced " +
                "Douglas to articulate what became known as the Freeport Doctrine.",
            city = "Freeport", state = "IL", latitude = 42.2967, longitude = -89.6212
        ),

        // ─── Tennessee ───────────────────────────────────────────────────────────
        Marker(
            markerId = "TN-0001", title = "Battle of Shiloh",
            description = "Fought April 6–7, 1862, the Battle of Shiloh was one of the first " +
                "major battles of the Civil War in the Western Theater. Union forces under " +
                "General Ulysses S. Grant suffered massive casualties but held the field, " +
                "preventing a Confederate recapture of western Tennessee.",
            city = "Hardin County", state = "TN", latitude = 35.1425, longitude = -88.3428
        ),
        Marker(
            markerId = "TN-0002", title = "Scopes Trial Courthouse",
            description = "In July 1925, the Dayton courthouse was the site of the famous " +
                "'Monkey Trial' in which high school teacher John Scopes was tried for teaching " +
                "evolution in violation of Tennessee's Butler Act. The trial became a landmark " +
                "in the debate between science and religion in American public life.",
            city = "Dayton", state = "TN", latitude = 35.4973, longitude = -85.0138
        ),

        // ─── Texas ───────────────────────────────────────────────────────────────
        Marker(
            markerId = "TX-0001", title = "The Alamo",
            description = "In February–March 1836, a small Texian garrison including James Bowie, " +
                "Davy Crockett, and William Barret Travis held the Alamo against a Mexican army " +
                "of more than 1,800. Their 13-day stand galvanized Texian independence forces, " +
                "who won the Texas Revolution six weeks later.",
            city = "San Antonio", state = "TX", latitude = 29.4260, longitude = -98.4861
        ),
        Marker(
            markerId = "TX-0002", title = "Spindletop Oil Discovery",
            description = "On January 10, 1901, drillers struck oil at Spindletop Hill near " +
                "Beaumont, producing the first great Texas oil gusher. The discovery launched " +
                "the modern petroleum industry and transformed the economy of Texas and the nation.",
            city = "Beaumont", state = "TX", latitude = 30.0510, longitude = -94.1150
        ),

        // ─── California ──────────────────────────────────────────────────────────
        Marker(
            markerId = "CA-0001", title = "Sutter's Mill Gold Discovery",
            description = "On January 24, 1848, James Marshall discovered gold at Sutter's Mill " +
                "on the American River, triggering the California Gold Rush of 1849 that brought " +
                "over 300,000 migrants to the state and dramatically accelerated California's " +
                "admission to the Union.",
            city = "Coloma", state = "CA", latitude = 38.7962, longitude = -120.8893
        ),
        Marker(
            markerId = "CA-0002", title = "Transcontinental Railroad Completion",
            description = "The ceremonial 'golden spike' was driven at Promontory Summit, Utah, " +
                "but the western terminus of the First Transcontinental Railroad was managed from " +
                "Sacramento. Central Pacific crews, largely Chinese immigrants, built eastward " +
                "from here, completing the link to the Union Pacific on May 10, 1869.",
            city = "Sacramento", state = "CA", latitude = 38.5816, longitude = -121.4944
        ),

        // ─── Georgia ─────────────────────────────────────────────────────────────
        Marker(
            markerId = "GA-0001", title = "Sherman's March to the Sea",
            description = "In November–December 1864, Union General William T. Sherman led " +
                "60,000 troops from Atlanta to Savannah, cutting a 60-mile-wide path of " +
                "destruction across Georgia. The campaign accelerated the Confederacy's collapse " +
                "by severing its supply lines and demoralizing the Southern population.",
            city = "Atlanta", state = "GA", latitude = 33.7490, longitude = -84.3880
        ),
        Marker(
            markerId = "GA-0002", title = "Martin Luther King Jr. Birthplace",
            description = "The Reverend Dr. Martin Luther King Jr., Nobel Peace Prize laureate " +
                "and leader of the American civil rights movement, was born at 501 Auburn Avenue " +
                "in Atlanta on January 15, 1929.",
            city = "Atlanta", state = "GA", latitude = 33.7554, longitude = -84.3741
        ),

        // ─── Ohio ─────────────────────────────────────────────────────────────────
        Marker(
            markerId = "OH-0001", title = "Wright Brothers First Flight Workshop",
            description = "Orville and Wilbur Wright designed and built their first powered " +
                "aircraft in their Dayton bicycle shop. Their successful flights at Kitty Hawk, " +
                "North Carolina on December 17, 1903 ushered in the age of aviation.",
            city = "Dayton", state = "OH", latitude = 39.7589, longitude = -84.1916
        ),

        // ─── Maryland ────────────────────────────────────────────────────────────
        Marker(
            markerId = "MD-0001", title = "Battle of Antietam",
            description = "On September 17, 1862, the Battle of Antietam near Sharpsburg was " +
                "the bloodiest single day in American military history, with approximately 23,000 " +
                "casualties. The Union victory gave President Lincoln the political footing to " +
                "issue the Emancipation Proclamation five days later.",
            city = "Sharpsburg", state = "MD", latitude = 39.4654, longitude = -77.7444
        ),
        Marker(
            markerId = "MD-0002", title = "Francis Scott Key — Star-Spangled Banner",
            description = "Francis Scott Key watched the British bombardment of Fort McHenry " +
                "from a ship in the Patapsco River on the night of September 13–14, 1814. " +
                "Seeing the American flag still flying at dawn, he wrote the poem that became " +
                "the national anthem.",
            city = "Baltimore", state = "MD", latitude = 39.2633, longitude = -76.5794
        ),

        // ─── Louisiana ───────────────────────────────────────────────────────────
        Marker(
            markerId = "LA-0001", title = "Battle of New Orleans",
            description = "On January 8, 1815, General Andrew Jackson's forces, including " +
                "regulars, militia, pirates, and free Black soldiers, decisively defeated a " +
                "veteran British army at the Battle of New Orleans — the final major battle " +
                "of the War of 1812, fought two weeks after the peace treaty was signed.",
            city = "Chalmette", state = "LA", latitude = 29.9433, longitude = -89.9756
        ),

        // ─── South Carolina ───────────────────────────────────────────────────────
        Marker(
            markerId = "SC-0001", title = "Fort Sumter — Start of Civil War",
            description = "Confederate artillery opened fire on the Union-held Fort Sumter in " +
                "Charleston Harbor on April 12, 1861, beginning the American Civil War. " +
                "The garrison surrendered after 34 hours of bombardment.",
            city = "Charleston", state = "SC", latitude = 32.7526, longitude = -79.8748
        ),

        // ─── Montana ─────────────────────────────────────────────────────────────
        Marker(
            markerId = "MT-0001", title = "Battle of the Little Bighorn",
            description = "On June 25–26, 1876, a combined force of Lakota, Northern Cheyenne, " +
                "and Arapaho warriors defeated the 7th Cavalry Regiment under Lt. Colonel " +
                "George Armstrong Custer. The battle, also called the Battle of Greasy Grass, " +
                "was one of the greatest victories for the Plains tribes against the US Army.",
            city = "Crow Agency", state = "MT", latitude = 45.5678, longitude = -107.4268
        ),

        // ─── Hawaii ──────────────────────────────────────────────────────────────
        Marker(
            markerId = "HI-0001", title = "Attack on Pearl Harbor",
            description = "On December 7, 1941, Imperial Japanese forces launched a surprise " +
                "aerial attack on the US naval base at Pearl Harbor, killing 2,403 Americans " +
                "and wounding 1,178. The attack led the United States to formally enter World War II.",
            city = "Pearl City", state = "HI", latitude = 21.3644, longitude = -157.9730
        ),

        // ─── Arizona ─────────────────────────────────────────────────────────────
        Marker(
            markerId = "AZ-0001", title = "Gunfight at the O.K. Corral",
            description = "On October 26, 1881, lawmen including Wyatt Earp, Virgil Earp, " +
                "Morgan Earp, and Doc Holliday clashed with the Clanton-McLaury gang in a " +
                "30-second gunfight near the O.K. Corral in Tombstone. The incident became the " +
                "most famous gunfight in the history of the American West.",
            city = "Tombstone", state = "AZ", latitude = 31.7126, longitude = -110.0676
        )
    )
}
